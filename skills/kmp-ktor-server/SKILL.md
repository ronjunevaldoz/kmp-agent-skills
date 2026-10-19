---
name: kmp-ktor-server
description: >
  How to structure a Ktor 3 server application: Application.module() composition, one
  module per feature, writing your own plugins with createApplicationPlugin and
  createRouteScopedPlugin (typed config, hooks, lifecycle events), configuration from
  ApplicationConfig/YAML, background work tied to the application lifecycle, dependency
  injection (Ktor DI or Koin), and testApplication tests. Use it for any Ktor backend,
  admin panel or game server. Not for auth details (kmp-ktor-auth-service), WebSocket
  servers (kmp-ktor-realtime) or the Ktor client (kmp-network-layer).
license: Apache-2.0
metadata:
  author: kmp-agent-skills
  last-updated: '2026-10-19'
  keywords:
    - Ktor server
    - Ktor plugin
    - createApplicationPlugin
    - createRouteScopedPlugin
    - Application.module
    - ApplicationConfig
    - application.yaml
    - EngineMain
    - ApplicationStarted
    - ApplicationStopping
    - Ktor DI
    - Koin Ktor
    - testApplication
    - backend structure
    - server architecture
---

## When to Use This Skill

Use this skill when you need to:
- Start a Ktor server, or restructure one that grew into a single large class
- Split a backend into feature modules with thin routes
- Write a reusable Ktor plugin with its own configuration and hooks
- Run background work (a ticker, a queue consumer) that starts and stops with the app
- Wire services with Ktor's DI or Koin, and test modules with `testApplication`

Do NOT use this skill when:
- You need login, JWT or sessions; use `kmp-ktor-auth-service`
- You are building a WebSocket or real-time server; use `kmp-ktor-realtime` on top of this one
- You are calling a server from a client; use `kmp-network-layer`

**Trigger keywords:** Ktor server, Ktor plugin, createApplicationPlugin,
createRouteScopedPlugin, Application.module, ApplicationConfig, application.yaml,
EngineMain, ApplicationStarted, ApplicationStopping, Ktor DI, Koin Ktor, testApplication,
backend structure, server architecture, god class server, restructure Ktor app.

**Freshness rule:** Ktor's plugin and DI APIs change between minor releases. Recheck
https://ktor.io/docs/server-custom-plugins.html and
https://ktor.io/docs/server-dependency-injection.html before implementing.
Minimum version: `ktor = "3.5.0"` in `libs.versions.toml`.

---

## Recommendation First

An application is **one entry point that installs plugins and feature modules**. The
`Application` owns the engine, configuration and lifecycle. Everything else is installed
into it. Nothing below it creates its own server or reads environment variables by hand.

```kotlin
// Application.kt
import io.ktor.server.application.Application
import io.ktor.server.application.install
import io.ktor.server.engine.EngineMain
import io.ktor.server.plugins.calllogging.CallLogging

fun main(args: Array<String>) = EngineMain.main(args)

fun Application.module() {
    install(CallLogging)
    wiring()        // services, from config (see Dependency Injection)
    healthRoutes()  // one function per feature module
    orderRoutes()
    adminRoutes()
}
```

```yaml
# src/main/resources/application.yaml
ktor:
  deployment:
    port: "$PORT:8080"
  application:
    modules:
      - com.example.ApplicationKt.module
orders:
  pageSize: 50
```

Each feature module is an `Application` extension in its own package. It installs only
what it needs, and declares only its own routes.

---

## Project Structure

```text
server/src/main/kotlin/com/example/
  Application.kt          main() and Application.module(): install, wire, modules
  Wiring.kt               services and stores, built from ApplicationConfig
  common/plugins/         the app's own reusable plugins (one file each)
  health/HealthRoutes.kt  fun Application.healthRoutes()
  orders/
    OrderRoutes.kt        fun Application.orderRoutes(): thin routes only
    OrderService.kt       business rules, no Ktor types
    OrderStore.kt         persistence behind an interface
```

Rules:
- Routes parse, call a service and respond. Business rules never import `io.ktor`.
- A feature never reaches into another feature's internals. It depends on that feature's service interface.
- Adding a feature adds one package and one line in `module()`.

---

## Writing Your Own Plugin

Write a plugin when a behaviour cuts across routes, or owns a resource with a lifecycle.
Give it a configuration class, read the configuration once, then register hooks.

```kotlin
import io.ktor.server.application.createApplicationPlugin

class RequestBudgetConfig {
    var maxPerMinute: Int = 600
    var header: String = "X-Budget-Remaining"
}

val RequestBudget = createApplicationPlugin(
    name = "RequestBudget",
    createConfiguration = ::RequestBudgetConfig,
) {
    // Configuration is mutable only while installing, so copy it out.
    val max = pluginConfig.maxPerMinute
    val header = pluginConfig.header
    val budget = SlidingWindowBudget(max)

    onCall { call ->
        val remaining = budget.take(call.request.local.remoteHost)
        call.response.headers.append(header, remaining.toString())
    }
}
```

### Hooks to know

| Hook | Use for |
|---|---|
| `onCall { call -> }` | every request: headers, timing, budgets |
| `onCallReceive { call -> transformBody { } }` | transforming request bodies |
| `onCallRespond { call -> transformBody { } }` | transforming responses |
| `on(CallSetup)`, `on(CallFailed)`, `on(ResponseSent)` | finer stages: setup, errors, after the response is sent |
| `on(MonitoringEvent(ApplicationStarted))` | starting background work |
| `on(MonitoringEvent(ApplicationStopping))` | stopping it: cancel, drain, flush |

Handlers can run concurrently. Shared state inside a plugin must be thread-safe.

### Exposing a service from a plugin

A plugin that owns a service puts it in `application.attributes`, behind a typed accessor.
Routes use the accessor and never touch the key.

```kotlin
import io.ktor.server.application.Application
import io.ktor.server.application.ApplicationStarted
import io.ktor.server.application.ApplicationStopping
import io.ktor.server.application.createApplicationPlugin
import io.ktor.server.application.hooks.MonitoringEvent
import io.ktor.util.AttributeKey
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch

class OutboxConfig {
    var flushEveryMillis: Long = 1_000
}

private val OutboxKey = AttributeKey<Outbox>("Outbox")

/** The app's outbox, for routes and other modules. */
val Application.outbox: Outbox get() = attributes[OutboxKey]

val OutboxPlugin = createApplicationPlugin("Outbox", ::OutboxConfig) {
    val every = pluginConfig.flushEveryMillis
    val outbox = Outbox()
    application.attributes.put(OutboxKey, outbox)
    var flusher: Job? = null

    on(MonitoringEvent(ApplicationStarted)) { app ->
        // Application is a CoroutineScope: this job ends with the app.
        flusher = app.launch {
            while (isActive) {
                outbox.flush()
                delay(every)
            }
        }
    }
    on(MonitoringEvent(ApplicationStopping)) {
        flusher?.cancel()
        outbox.flushNow()
    }
}
```

### Route-scoped plugins

Use `createRouteScopedPlugin` when a behaviour applies to some routes only, such as an
audit log on the admin routes.

```kotlin
import io.ktor.server.application.createRouteScopedPlugin
import io.ktor.server.auth.principal
import io.ktor.server.auth.UserIdPrincipal

class AuditConfig {
    var sink: AuditSink = AuditSink.None
}

val Audit = createRouteScopedPlugin("Audit", ::AuditConfig) {
    val sink = pluginConfig.sink
    onCall { call ->
        val who = call.principal<UserIdPrincipal>()?.name ?: "anonymous"
        sink.record(who, call.request.local.method.value, call.request.local.uri)
    }
}

// routing { route("/admin") { install(Audit) { sink = auditSink }; adminEndpoints() } }
```

---

## Configuration

Read every setting from `ApplicationConfig`. Never parse `System.getenv` by hand.
YAML values can name an environment variable with a default, for example `"$PORT:8080"`.

```kotlin
import io.ktor.server.application.Application

data class OrderSettings(val pageSize: Int, val databaseUrl: String?)

fun Application.orderSettings(): OrderSettings {
    val config = environment.config
    return OrderSettings(
        pageSize = config.property("orders.pageSize").getString().toInt(),
        databaseUrl = config.propertyOrNull("orders.databaseUrl")?.getString(),
    )
}
```

A plugin can read its own section by passing `configurationPath` to
`createApplicationPlugin`, with a configuration class that takes an `ApplicationConfig`.

---

## Dependency Injection

Default to **Ktor's own DI** (`ktor-server-di`). Use Koin's Ktor plugin when the project
already uses Koin everywhere. Never resolve services from a global inside a route.

```kotlin
import io.ktor.server.application.Application
import io.ktor.server.plugins.di.dependencies
import io.ktor.server.response.respond
import io.ktor.server.routing.get
import io.ktor.server.routing.routing

fun Application.wiring() {
    val settings = orderSettings()
    dependencies {
        provide<OrderStore> {
            settings.databaseUrl?.let(::PostgresOrderStore) ?: InMemoryOrderStore()
        }
        // A constructor reference: Ktor resolves its parameters by type.
        provide<OrderService>(::OrderService)
    }
}

fun Application.orderRoutes() {
    val orders: OrderService by dependencies
    routing {
        get("/orders") { call.respond(orders.page(call.parameters["after"])) }
    }
}
```

`AutoCloseable` dependencies close when the app stops, in reverse order of declaration.
Add `cleanup { }` after `provide` for anything else.

---

## Lifecycle

- Start background work in `ApplicationStarted`, and launch it in the `Application` scope.
- Stop it in `ApplicationStopping`: cancel, drain queues, flush writes.
- Let Ktor's own shutdown hook stop the engine. Don't turn it off and add a JVM hook.
- Expose readiness as a route (`/health`) that reads the services' state, not a flag a hook sets.

---

## Testing

Test each module with `testApplication`. Register fakes instead of calling `wiring()`.

```kotlin
import io.ktor.client.request.get
import io.ktor.client.statement.bodyAsText
import io.ktor.http.HttpStatusCode
import io.ktor.server.config.MapApplicationConfig
import io.ktor.server.plugins.di.dependencies
import io.ktor.server.testing.testApplication
import kotlin.test.Test
import kotlin.test.assertEquals

class OrderRoutesTest {
    @Test
    fun `lists the first page`() = testApplication {
        environment { config = MapApplicationConfig("orders.pageSize" to "2") }
        application {
            dependencies { provide<OrderService> { OrderService(InMemoryOrderStore(seed = 3)) } }
            orderRoutes()
        }
        val response = client.get("/orders")
        assertEquals(HttpStatusCode.OK, response.status)
        assertEquals(2, response.bodyAsText().count { it == '{' })
    }

    @Test
    fun `the budget header counts down`() = testApplication {
        application {
            install(RequestBudget) { maxPerMinute = 2 }
            healthRoutes()
        }
        assertEquals("1", client.get("/health").headers["X-Budget-Remaining"])
        assertEquals("0", client.get("/health").headers["X-Budget-Remaining"])
    }
}
```

Test a plugin by installing it alone with a tiny route. Test services without Ktor at all.

---

## Common Anti-Patterns

- **The god class.** One class holds sessions, rules, persistence and every feature, so
  adding a feature means editing it in several places. Split it into feature modules and
  plugins, so each feature lives in its own package.
- **A component that creates the server.** A transport, client or service that calls
  `embeddedServer` and takes the app's routes as a lambda turns the app inside out. The
  `Application` owns the engine, and everything else is installed into it.
- **Hand-parsed environment variables.** Settings read with `System.getenv` scattered
  through the code bypass `ApplicationConfig` and test overrides. Put them in
  `application.yaml`, with `"$VAR:default"` where needed.
- **Lifecycle outside `monitor`.** A JVM shutdown hook, or turning off Ktor's own, races
  the engine's stop. Use `ApplicationStarted` and `ApplicationStopping`.
- **Fat routes.** Business rules inside `get { }` can't be tested without HTTP. Call a
  service with no Ktor types.
- **Mutable plugin config after install.** Reading `pluginConfig` inside a hook sees
  values that may change. Copy them into locals when the plugin is installed.
- **Globals as DI.** An `object` registry read from routes hides dependencies and breaks
  tests. Use `dependencies` or Koin.

---

## Related Skills

- `kmp-ktor-auth-service`: authentication, route guards and token flows inside this structure.
- `kmp-ktor-realtime`: WebSocket servers and authoritative loops, built as plugins from this skill.
- `kmp-clean-architecture`: module boundaries between the server, shared models and features.
- `kmp-coroutines-flow-patterns`: scopes, cancellation and structured concurrency behind the lifecycle rules.
- `kmp-kotlin-rpc`: typed RPC endpoints when the client is also Kotlin.
- `kmp-network-layer`: the client side of the same API.

---

## Output Style

When asked to build or restructure a Ktor server, respond in this order:
1. Give the `module()` layout and the feature packages.
2. Show the plugins it needs, with configuration classes.
3. Show the configuration and DI wiring.
4. Show one `testApplication` test per module.
5. Name the anti-patterns the current code has, if any.

Keep answers about structure. Auth goes to `kmp-ktor-auth-service`, WebSockets to `kmp-ktor-realtime`.

---

## Changelog

| Date | Change |
|---|---|
| 2026-10-19 | Initial release: module composition, custom plugins, configuration, DI, lifecycle, testing and anti-patterns (issue #23). |
