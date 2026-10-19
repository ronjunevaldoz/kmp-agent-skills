---
name: kmp-ktor-realtime
description: >
  Real-time WebSocket servers on Ktor 3: install(WebSockets) settings, a per-connection
  session with a bounded outbound channel (backpressure, slow-client handling), typed
  message routing by registration instead of one central when, features that register
  their own handlers, a single-threaded authoritative loop (a game tick or a matching
  engine) fed by a bounded inbound queue, broadcast and fan-out, graceful drain on
  ApplicationStopping, and tests with testApplication's WebSocket client. Builds on
  kmp-ktor-server. Not for HTTP routes, auth or the client side.
license: Apache-2.0
metadata:
  author: kmp-agent-skills
  last-updated: '2026-10-19'
  keywords:
    - WebSocket server
    - Ktor WebSockets
    - real-time server
    - game server
    - multiplayer server
    - tick loop
    - authoritative server
    - message router
    - broadcast
    - backpressure
    - slow client
    - session lifecycle
    - graceful shutdown
---

## When to Use This Skill

Use this skill when you need to:
- Serve WebSocket clients from Ktor: chat, live dashboards, collaborative editing, multiplayer games
- Route many message types to handlers without one central `when`
- Run an authoritative loop (a game tick, an order book) on one thread, fed by client messages
- Broadcast to many sessions without one slow client stalling the rest
- Stop cleanly: drain queues, notify clients, save state

Do NOT use this skill when:
- You only need request/response HTTP; use `kmp-ktor-server`
- You need server-sent events to a browser; see `kmp-network-layer`'s SSE section
- You need login or tokens; use `kmp-ktor-auth-service`, then authenticate the socket's first message or upgrade request

**Trigger keywords:** WebSocket server, Ktor WebSockets, real-time server, game server,
multiplayer server, tick loop, authoritative server, message router, broadcast,
backpressure, slow client, session lifecycle, graceful shutdown, webSocket route.

**Freshness rule:** Ktor's WebSockets plugin changes between releases. Recheck
https://ktor.io/docs/server-websockets.html before implementing.
Minimum version: `ktor = "3.5.0"` in `libs.versions.toml`, with `kotlinx-coroutines` 1.9 or later.

---

## Recommendation First

Split the server into four parts, each with one job:

| Part | Job |
|---|---|
| **Connection** | one per socket: reads frames, writes from a bounded outbound queue |
| **SessionHub** | the open connections, by id: send, broadcast, close |
| **MessageRouter** | message type → handler, filled by features as they register |
| **Simulation** | the authoritative loop on one thread: drains the inbound queue, runs handlers, steps state, broadcasts |

The socket handler never runs game or business rules. It decodes a message and offers it
to the simulation's queue. Everything that changes state runs on the simulation's thread,
so handlers need no locks and stay deterministic.

```kotlin
import io.ktor.server.application.Application
import io.ktor.server.application.install
import io.ktor.server.websocket.WebSockets
import io.ktor.server.websocket.pingPeriod
import io.ktor.server.websocket.timeout
import kotlin.time.Duration.Companion.seconds

fun Application.module() {
    // WebSockets first: the Realtime plugin adds a webSocket route.
    install(WebSockets) {
        pingPeriod = 15.seconds
        timeout = 30.seconds
        maxFrameSize = 64 * 1024L
        masking = false
    }
    install(Realtime) {
        ticksPerSecond = 20
        codec = JsonMessageCodec
        features(Chat, Rooms, Movement)
    }
}
```

---

## Typed Routing by Registration

Each feature registers the message types it handles. The router dispatches by class, and
refuses a second handler for the same type, so two features can't silently compete.

```kotlin
import kotlin.reflect.KClass

class MessageRouter<S, M : Any> {
    private val handlers = HashMap<KClass<out M>, (S, M) -> Unit>()

    fun <T : M> on(type: KClass<T>, handler: (S, T) -> Unit) {
        require(type !in handlers) { "${type.simpleName} already has a handler" }
        @Suppress("UNCHECKED_CAST")
        handlers[type] = handler as (S, M) -> Unit
    }

    inline fun <reified T : M> on(noinline handler: (S, T) -> Unit) = on(T::class, handler)

    /** Runs the handler for [message]; false when no feature handles its type. */
    fun dispatch(session: S, message: M): Boolean =
        handlers[message::class]?.let { it(session, message); true } ?: false
}

/** A feature: its state, and the messages it handles. Adding one touches only its own file. */
fun interface RealtimeFeature {
    fun FeatureScope.install()
}

class FeatureScope(
    val router: MessageRouter<SessionId, ClientMessage>,
    val hub: SessionHub,
) {
    internal val onLeave = mutableListOf<(SessionId) -> Unit>()
    internal val onTick = mutableListOf<(Long) -> Unit>()
    fun onLeave(block: (SessionId) -> Unit) { onLeave += block }
    fun onTick(block: (tick: Long) -> Unit) { onTick += block }
}

val Chat = RealtimeFeature {
    val rooms = ChatRooms()
    router.on<ClientMessage.Say> { from, msg -> rooms.say(from, msg.text, hub) }
    router.on<ClientMessage.Join> { from, msg -> rooms.join(from, msg.room) }
    onLeave { who -> rooms.leaveAll(who) }
}
```

Keep message types in a sealed hierarchy per feature, or give each feature an id range,
so the protocol stays stable as features are added.

---

## Connection and SessionHub

Every connection has a **bounded** outbound channel and its own writer coroutine.
Senders use `trySend`, so a full queue never blocks the simulation. A client that falls
too far behind is closed rather than buffered forever.

```kotlin
import io.ktor.server.websocket.DefaultWebSocketServerSession
import io.ktor.websocket.CloseReason
import io.ktor.websocket.Frame
import io.ktor.websocket.close
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.atomic.AtomicLong
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.launch

@JvmInline value class SessionId(val value: Long)

class Connection(
    val id: SessionId,
    private val socket: DefaultWebSocketServerSession,
    capacity: Int = 256,
) {
    private val outbound = Channel<ByteArray>(capacity)
    private val writer = socket.launch {
        for (bytes in outbound) socket.send(Frame.Binary(true, bytes))
    }

    /** Queues [bytes]; false when the client has fallen too far behind. */
    fun offer(bytes: ByteArray): Boolean = outbound.trySend(bytes).isSuccess

    fun closeLater(reason: CloseReason) {
        socket.launch {
            outbound.close()
            writer.join()
            socket.close(reason)
        }
    }
}

/** Open so tests can record what features send, without sockets. */
open class SessionHub {
    private val nextId = AtomicLong(1)
    private val open = ConcurrentHashMap<SessionId, Connection>()

    fun open(socket: DefaultWebSocketServerSession): Connection =
        Connection(SessionId(nextId.getAndIncrement()), socket).also { open[it.id] = it }

    fun remove(id: SessionId) { open.remove(id) }

    open fun send(to: SessionId, bytes: ByteArray) {
        val connection = open[to] ?: return
        if (!connection.offer(bytes)) kick(to, "too slow")
    }

    open fun broadcast(bytes: ByteArray, except: SessionId? = null) {
        for ((id, connection) in open) if (id != except && !connection.offer(bytes)) kick(id, "too slow")
    }

    open fun kick(id: SessionId, why: String) {
        open.remove(id)?.closeLater(CloseReason(CloseReason.Codes.VIOLATED_POLICY, why))
    }

    fun closeAll(reason: CloseReason) {
        for (id in open.keys.toList()) open.remove(id)?.closeLater(reason)
    }
}
```

---

## The Authoritative Loop

One coroutine on a **single-thread** dispatcher owns all state. Sockets feed it through a
bounded inbound channel. Each tick drains the queue, runs handlers, steps state and sends.

```kotlin
import kotlin.time.TimeSource
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive
import kotlinx.coroutines.withContext

sealed interface Inbound {
    data class Message(val from: SessionId, val message: ClientMessage) : Inbound
    data class Left(val who: SessionId) : Inbound
}

class Simulation(
    private val scope: FeatureScope,
    ticksPerSecond: Int,
    queueCapacity: Int = 8_192,
) {
    /** The only thread that touches simulation state. */
    val dispatcher = Dispatchers.Default.limitedParallelism(1)
    private val inbound = Channel<Inbound>(queueCapacity)
    private val tickMillis = 1_000L / ticksPerSecond
    var tick = 0L
        private set

    /** From any socket coroutine; false when the server is overloaded. */
    fun offer(event: Inbound): Boolean = inbound.trySend(event).isSuccess

    suspend fun run(onStop: () -> Unit) = withContext(dispatcher) {
        try {
            while (currentCoroutineContext().isActive) {
                val started = TimeSource.Monotonic.markNow()
                step()
                delay((tickMillis - started.elapsedNow().inWholeMilliseconds).coerceAtLeast(0))
            }
        } finally {
            withContext(NonCancellable) { drain(); onStop() }
        }
    }

    /** One tick. Public so tests can step without sockets or clocks. */
    fun step() {
        drain()
        tick++
        scope.onTick.forEach { it(tick) }
    }

    private fun drain() {
        while (true) {
            when (val event = inbound.tryReceive().getOrNull() ?: return) {
                is Inbound.Message -> if (!scope.router.dispatch(event.from, event.message)) {
                    scope.hub.kick(event.from, "unknown message")
                }
                is Inbound.Left -> scope.onLeave.forEach { it(event.who) }
            }
        }
    }
}
```

Blocking work (database writes, files) never runs on this dispatcher. Hand it to an IO
coroutine with a copy of the data, and post the result back as an `Inbound` event.

---

## The Plugin and the Socket Route

```kotlin
import io.ktor.server.application.ApplicationStarted
import io.ktor.server.application.ApplicationStopping
import io.ktor.server.application.createApplicationPlugin
import io.ktor.server.application.hooks.MonitoringEvent
import io.ktor.server.routing.routing
import io.ktor.server.websocket.webSocket
import io.ktor.websocket.CloseReason
import io.ktor.websocket.Frame
import io.ktor.websocket.close
import io.ktor.websocket.readBytes
import kotlinx.coroutines.Job
import kotlinx.coroutines.launch

class RealtimeConfig {
    var path: String = "/ws"
    var ticksPerSecond: Int = 20
    var codec: MessageCodec = JsonMessageCodec
    internal val installed = mutableListOf<RealtimeFeature>()
    fun features(vararg list: RealtimeFeature) { installed += list }
}

val Realtime = createApplicationPlugin("Realtime", ::RealtimeConfig) {
    val codec = pluginConfig.codec
    val hub = SessionHub()
    val scope = FeatureScope(MessageRouter(), hub)
    pluginConfig.installed.forEach { feature -> with(feature) { scope.install() } }
    val simulation = Simulation(scope, pluginConfig.ticksPerSecond)
    var loop: Job? = null

    application.routing {
        webSocket(pluginConfig.path) {
            val connection = hub.open(this)
            try {
                for (frame in incoming) {
                    if (frame !is Frame.Binary) continue
                    val message = codec.decode(frame.readBytes())
                    if (message == null) {
                        close(CloseReason(CloseReason.Codes.CANNOT_ACCEPT, "bad message"))
                        break
                    }
                    if (!simulation.offer(Inbound.Message(connection.id, message))) {
                        close(CloseReason(CloseReason.Codes.TRY_AGAIN_LATER, "server busy"))
                        break
                    }
                }
            } finally {
                hub.remove(connection.id)
                simulation.offer(Inbound.Left(connection.id))
            }
        }
    }
    on(MonitoringEvent(ApplicationStarted)) { app ->
        loop = app.launch { simulation.run { hub.closeAll(CloseReason(CloseReason.Codes.GOING_AWAY, "shutting down")) } }
    }
    on(MonitoringEvent(ApplicationStopping)) { loop?.cancel() }
}
```

On stop, the loop's `finally` drains what is queued, then closes every session with
`GOING_AWAY`. Put "save everyone" in the same place, so it runs exactly once.

---

## Testing

Test features by stepping the simulation, with no sockets. Test the wiring once with
`testApplication` and a real WebSocket client.

```kotlin
import io.ktor.client.plugins.websocket.WebSockets
import io.ktor.client.plugins.websocket.webSocket
import io.ktor.server.application.install
import io.ktor.server.testing.testApplication
import io.ktor.websocket.Frame
import io.ktor.websocket.readBytes
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import io.ktor.server.websocket.WebSockets as ServerWebSockets

/** Records what features send, instead of writing to sockets. */
class RecordingHub : SessionHub() {
    val sent = mutableMapOf<SessionId, MutableList<ByteArray>>()
    val kicked = mutableListOf<SessionId>()
    override fun send(to: SessionId, bytes: ByteArray) { sent.getOrPut(to) { mutableListOf() } += bytes }
    override fun kick(id: SessionId, why: String) { kicked += id }
}

class ChatTest {
    @Test
    fun `a message reaches the room on the next tick`() {
        val hub = RecordingHub()
        val scope = FeatureScope(MessageRouter(), hub)
        with(Chat) { scope.install() }
        val simulation = Simulation(scope, ticksPerSecond = 20)

        simulation.offer(Inbound.Message(SessionId(1), ClientMessage.Join("lobby")))
        simulation.offer(Inbound.Message(SessionId(2), ClientMessage.Join("lobby")))
        simulation.offer(Inbound.Message(SessionId(1), ClientMessage.Say("hi")))
        simulation.step()

        assertEquals(1, hub.sent[SessionId(2)]?.size)
        assertEquals(emptyList(), hub.kicked)
    }

    @Test
    fun `a second handler for the same type is refused`() {
        val router = MessageRouter<SessionId, ClientMessage>()
        router.on<ClientMessage.Say> { _, _ -> }
        assertFalse(runCatching { router.on<ClientMessage.Say> { _, _ -> } }.isSuccess)
    }

    @Test
    fun `a client sees its own echo over a socket`() = testApplication {
        application {
            install(ServerWebSockets)
            install(Realtime) { features(Echo) }
        }
        val client = createClient { install(WebSockets) }
        client.webSocket("/ws") {
            send(Frame.Binary(true, JsonMessageCodec.encode(ClientMessage.Say("ping"))))
            val reply = incoming.receive() as Frame.Binary
            assertEquals(ServerMessage.Said("ping"), JsonMessageCodec.decodeServer(reply.readBytes()))
        }
    }
}
```

Also test overload: fill the inbound queue and assert the socket closes with
`TRY_AGAIN_LATER`. Also test a slow client: stop reading on one client and assert the
others still receive, and the slow one is kicked.

---

## Common Anti-Patterns

- **One central `when` over every message.** Every new message edits the same function,
  and features conflict. Register handlers per feature in a `MessageRouter`.
- **Rules on the socket coroutine.** Handling messages where they are read makes state
  shared across threads. Offer them to the simulation's queue and handle them on its thread.
- **Unbounded queues.** `Channel.UNLIMITED` inbound or outbound turns a burst or a slow
  client into a memory leak. Bound both, then refuse or kick when they fill.
- **Suspending sends from the loop.** `send` on a socket inside the tick stalls everyone
  behind one client. Use `trySend` into the connection's own queue.
- **Blocking IO on the simulation thread.** A database write inside a tick freezes the
  world. Copy the data, write on `Dispatchers.IO`, and post the result back as an event.
- **The transport owns the server.** A WebSocket class that calls `embeddedServer` and
  takes the app's routes as a lambda inverts the app. Install WebSockets and the
  realtime plugin into the `Application` (`kmp-ktor-server`).
- **Shutdown in a JVM hook.** Saving from `Runtime.addShutdownHook` races the engine's
  stop. Drain in the loop's `finally`, triggered by `ApplicationStopping`.

---

## Related Skills

- `kmp-ktor-server`: the application, plugin and lifecycle structure this builds on.
- `kmp-ktor-auth-service`: authenticating the upgrade request or the first message.
- `kmp-coroutines-flow-patterns`: channels, single-thread dispatchers and cancellation.
- `kmp-kotlin-rpc`: when request/response RPC fits better than a socket protocol.
- `kmp-unit-testing`: fakes and test structure for features stepped without sockets.

---

## Output Style

When asked to build or restructure a real-time server, respond in this order:
1. Give the four parts and where each lives.
2. Show the router and one feature registering its handlers.
3. Show the connection, the hub and the loop.
4. Show the plugin that wires them, and its stop path.
5. Show one stepped feature test and one `testApplication` socket test.

Keep answers about the real-time path. HTTP structure goes to `kmp-ktor-server`.

---

## Changelog

| Date | Change |
|---|---|
| 2026-10-19 | Initial release: connections with bounded queues, typed routing by registration, the single-threaded loop, the plugin, graceful drain and tests (issue #23). |
