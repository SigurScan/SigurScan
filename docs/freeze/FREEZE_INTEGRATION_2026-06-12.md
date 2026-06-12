# SigurScan Freeze Integration - 2026-06-12

## Branch

`feature/freeze-integration-2026-06-12`

Base worktree: `/Users/vaduvageorge/AndroidStudioProjects/SigurScan-worktrees/fable-freeze-handoff`

## Scope Integrated

- Fable offer chain handoff from `feature/fable-freeze-handoff-2026-06-12`.
- PR1-PR6 offer flow material present on the branch.
- Registry verification adapters from PR4.
- Legal layer from PR5.
- Async web-claim path from PR6.
- Knowledge v3 offer corpus and OP-08/OP-09 material from Fable handoff.
- Impersonation research pack merged into runtime knowledge:
  - `IMP-13` utility/telco impersonation family.
  - 13 impersonation families total.
  - 487 family signals.
  - 50 verification sources.
  - 183 source references.
  - 51 family false-positive guards.
  - 139 research fixtures.
- Root offer handoff docs moved under `docs/fable_handoff/`.

## Evidence

- `python3 -m pytest backend/test_impersonation_knowledge_builder.py backend/test_scam_atlas_impersonation.py backend/test_scam_atlas_contract.py -q`
  - Result: `14 passed`.
- `python3 -m pytest backend -q`
  - Result: `655 passed, 1 warning`.
- `JAVA_HOME="/Applications/Android Studio.app/Contents/jbr/Contents/Home" ./gradlew :app:testDebugUnitTest :app:assembleDebug`
  - Result: `BUILD SUCCESSFUL`.
- `git diff --check`
  - Result: clean.
- Secret scan on changed/untracked integration files:
  - No real secrets found; matches were corpus/test words such as `password`, `token`, and env var names in tests.

## Important Non-Claims

- This does not mark the full product freeze complete.
- Live Cloud Run smoke, Android emulator E2E, domain/DNS verification, and Play-ready operational checks still need separate evidence.
- Invoice scan remains present on `main`; old DeepSeek invoice stash is older than current `main` and should not be blindly applied.
- Main was not modified by this integration branch.

## Next Freeze Checks

1. Review and merge/squash this branch only after inspecting the combined PR1-PR6 diff.
2. Run Cloud Run live smoke with API key on:
   - normal message/link scan,
   - offer scan,
   - invoice scan,
   - impersonation text case,
   - dangerous Web Risk control.
3. Run Android emulator E2E against the Cloud Run base URL.
4. Confirm domain mapping and API base URL final state.
5. Only then mark P0-P6 freeze rows as green.
