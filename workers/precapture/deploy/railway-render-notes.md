# Railway / Render notes

Use Docker deployment, not a plain Node runtime, because Playwright/Chromium needs browser dependencies.

Recommended settings:
- Start command: leave Dockerfile ENTRYPOINT/CMD or override with `--email-source /input ...`.
- Memory: 1GB minimum, 2GB recommended.
- Concurrency: 1-2.
- Secrets: SUPABASE_URL, SUPABASE_SERVICE_KEY.
- Do not expose it as a public website unless you add authentication and queueing.

For production, prefer a worker/job schedule over an always-on public service.
