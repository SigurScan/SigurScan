# Test runner contract

Pseudo-flow:

```kotlin
for (case in testCases) {
    val input = loadFixture(case.fixturePaths.first())
    val localSnapshot = scanner.scanLocal(input)
    val providerSignals = mockProviderLoader.load(case.id)
    val snapshot = evidenceSnapshotBuilder.merge(localSnapshot, providerSignals)
    val gate = evidenceGate.evaluate(snapshot)

    assertEquals(case.expectedDecision, gate.decision.name)
    case.expectedSignals.forEach { assertSignalPresent(snapshot, it) }
}
```

Rules:

- Do not use live provider adapters for this pack.
- Do not make network requests for `.test`, `.invalid`, or `.example` URLs.
- Treat `groundTruthIsScam=false` as a false-positive guard even when the expected action is `NO_REPLY` for OTP/privacy safety.
- `groundTruthIsScam=null` means ambiguous/unknown edge case.
```
