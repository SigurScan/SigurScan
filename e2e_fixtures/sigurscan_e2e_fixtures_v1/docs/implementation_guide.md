# Cum se leagă pachetul de aplicația reală

## Android

```kotlin
@ParameterizedTest
@MethodSource("fixtureCases")
fun runEvidenceGateE2E(case: FixtureCase) {
    val bytes = assetLoader.read(case.fixturePath)
    val input = InputFactory.from(case.inputType, bytes)

    val localSnapshot = scanPipeline.runLocal(input)
    val mock = providerMockLoader.read(case.providerMockPath)
    backendMock.install(case.id, mock)

    val result = scanPipeline.runFull(input, providerMode = MOCKED)

    assertEquals(case.expectedDecision, result.gateResult.decision.name)
    assertEquals(case.expectedUserLabel, result.userResult.label)

    case.primaryUrlExpected?.let {
        assertEquals(it, result.snapshot.primaryUrl?.normalizedUrl)
    }

    assertTrue(result.snapshot.signals.map { it.kind.name }.containsAll(case.expectedSignalKinds))
}
```

## Backend

```kotlin
@Test
fun contractCase() {
    val fixture = loadFixtureCase("DURL002")
    val providers = loadProviderMock(fixture.providerMockPath)
    val snapshot = orchestrator.run(fixture.input, providers)
    val gate = evidenceGate.evaluate(snapshot)
    assertThat(gate.decision).isEqualTo(GateDecision.DO_NOT_CONTINUE)
}
```

## Atenție
- Cazurile legit folosesc uneori domenii reale oficiale, dar tot trebuie rulate cu mocks ca să nu lovești servicii externe în CI.
- Cazurile de scam folosesc `.test` și `.invalid`; acestea sunt safe și nu trebuie rezolvate DNS.
- `RAG_EXPLANATION` nu se testează ca sursă de decizie; testează doar că explicația nu schimbă verdictul.
