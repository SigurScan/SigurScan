# Android Audio Capture Policy - 2026-06-14

SigurScan must not claim production audio/call ASR until all of these are true:

- The feature is explicitly enabled by a build/runtime flag.
- The user gives explicit consent before capture.
- The user accepts a privacy disclosure for audio processing.
- An on-device ASR model is packaged, versioned, and tested.
- The app does not perform hidden call recording.
- The feature has real-device QA evidence.

Current state:

- Audio capture is blocked by `AudioSafetyPolicy` by default.
- Android has an on-device `AudioEvidenceEngine` plus `AudioTranscriptEvidence` for Romanian call transcripts; it extracts only decision signals, stores no raw transcript/audio in the result, and does not call a server.
- A user-selected/current transcript can be analyzed locally from the Radar UI even while capture remains blocked.
- The realistic call-transcript fixture pack is covered: `34/34` scam transcripts produce actionable local evidence and none retain raw audio.
- Model readiness now targets the Whisper.cpp package layout under `assets/asr/whispercpp/` and requires `model-manifest.json` plus `ggml-model.bin`; a random/non-empty assets directory cannot mark ASR as ready.
- `WhisperCppAsrEngine` is wired as the Android replacement path and feeds transcripts into the local audio evidence engine without retaining raw audio bytes.
- No Whisper.cpp native library or production Romanian model binary is bundled yet.
- Vosk is no longer the selected Android ASR path because the official Vosk model list checked on 2026-06-14 does not provide a Romanian model: `https://alphacephei.com/vosk/models`.
- No hidden call recording is implemented.
- The Android manifest does not request `android.permission.RECORD_AUDIO`.
- The current UI provides real local transcript analysis and a separate readiness gate; it is not an audio capture feature.
- PR-9/PR-10 remain gated until the above requirements are implemented and verified.
