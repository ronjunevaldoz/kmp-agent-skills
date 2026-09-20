# Common KMP Anti-Patterns

Use this checklist during planning or review only when the task touches these areas.

- **DTO leaking to ViewModel/UI**: map transport DTOs to domain or presentation types.
- **Network result in MVI state**: map `NetworkResult<T>` into UI/domain state.
- **Direct database access in ViewModel**: use a repository or domain boundary.
- **Unstructured `GlobalScope` work**: use an owned scope and cancellation path.
- **Mutable `LaunchedEffect` key for one-shot events**: use an event/effect stream with
  appropriate delivery semantics.
- **Loading state not reset on failure**: include a terminal error state or clear loading.
- **Durable state kept only in `remember`**: choose a state holder that survives the required
  lifecycle.
- **ViewModel for ephemeral UI state**: local tooltip/dropdown state usually belongs near UI.
- **Preview impossible due to hidden state**: inject state and callbacks at the composable boundary.
- **Identical `actual` implementations**: move platform-independent logic to `commonMain`.
- **Pass-through repository without resilience/cache policy**: define freshness, failure, and
  offline behavior appropriate to the feature.
- **Network calls from an observation Flow**: keep reads reactive and make refresh an explicit
  operation.
