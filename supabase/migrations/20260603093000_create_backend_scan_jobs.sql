-- Backend-only orchestration jobs for SigurScan scan polling.
-- Clients never read/write this table directly; they call the backend.

create table if not exists public.scan_jobs (
  scan_id text primary key,
  status text not null default 'scanning',
  input_type text,
  source_channel text,
  payload jsonb not null default '{}'::jsonb,
  expires_at timestamptz,
  updated_at timestamptz not null default now(),
  created_at timestamptz not null default now()
);

create index if not exists scan_jobs_status_idx on public.scan_jobs (status);
create index if not exists scan_jobs_expires_at_idx on public.scan_jobs (expires_at);
create index if not exists scan_jobs_updated_at_idx on public.scan_jobs (updated_at desc);

alter table public.scan_jobs enable row level security;

drop trigger if exists set_scan_jobs_updated_at on public.scan_jobs;
create trigger set_scan_jobs_updated_at
before update on public.scan_jobs
for each row execute function public.set_updated_at();

revoke all on table public.scan_jobs from anon;
revoke all on table public.scan_jobs from authenticated;
