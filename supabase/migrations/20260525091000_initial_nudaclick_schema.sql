create extension if not exists pgcrypto;

create table if not exists public.scan_events (
  id uuid primary key default gen_random_uuid(),
  scan_id text not null unique,
  event_type text not null default 'scan_completed',
  input_type text not null,
  source_channel text,
  risk_score integer not null default 0 check (risk_score between 0 and 100),
  risk_level text,
  user_risk_level text,
  user_risk_label text,
  detected_family_id text,
  detected_family text,
  claimed_brand text,
  predicted_is_scam boolean,
  signal_ids text[] not null default '{}',
  url_count integer not null default 0 check (url_count >= 0),
  urls jsonb not null default '[]'::jsonb,
  redacted_text_snippet text,
  evidence jsonb not null default '{}'::jsonb,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.scan_feedback (
  id uuid primary key default gen_random_uuid(),
  scan_id text not null,
  feedback text not null check (feedback in ('correct', 'false_positive', 'false_negative', 'uncertain')),
  actual_is_scam boolean,
  predicted_is_scam boolean,
  predicted_risk_score integer check (predicted_risk_score is null or predicted_risk_score between 0 and 100),
  risk_level text,
  signal_ids text[] not null default '{}',
  source_channel text,
  notes text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.url_reputation_cache (
  url_hash text primary key,
  canonical_url text,
  registered_domain text,
  verdict text not null default 'unknown',
  risk_score integer not null default 0 check (risk_score between 0 and 100),
  confidence numeric(5, 4) not null default 0 check (confidence >= 0 and confidence <= 1),
  sources jsonb not null default '{}'::jsonb,
  details jsonb not null default '{}'::jsonb,
  expires_at timestamptz,
  updated_at timestamptz not null default now(),
  created_at timestamptz not null default now()
);

create table if not exists public.app_devices (
  id uuid primary key default gen_random_uuid(),
  device_id_hash text unique,
  platform text,
  app_version text,
  consent jsonb not null default '{}'::jsonb,
  first_seen_at timestamptz not null default now(),
  last_seen_at timestamptz not null default now()
);

create table if not exists public.admin_audit_log (
  id uuid primary key default gen_random_uuid(),
  actor_id text,
  action text not null,
  target_type text,
  target_id text,
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists scan_events_created_at_idx on public.scan_events (created_at desc);
create index if not exists scan_events_scan_id_idx on public.scan_events (scan_id);
create index if not exists scan_events_input_type_idx on public.scan_events (input_type);
create index if not exists scan_events_detected_family_idx on public.scan_events (detected_family_id);
create index if not exists scan_events_signal_ids_idx on public.scan_events using gin (signal_ids);

create index if not exists scan_feedback_created_at_idx on public.scan_feedback (created_at desc);
create index if not exists scan_feedback_scan_id_idx on public.scan_feedback (scan_id);
create index if not exists scan_feedback_feedback_idx on public.scan_feedback (feedback);
create index if not exists scan_feedback_signal_ids_idx on public.scan_feedback using gin (signal_ids);

create index if not exists url_reputation_cache_domain_idx on public.url_reputation_cache (registered_domain);
create index if not exists url_reputation_cache_expires_at_idx on public.url_reputation_cache (expires_at);
create index if not exists url_reputation_cache_updated_at_idx on public.url_reputation_cache (updated_at desc);

create index if not exists app_devices_last_seen_at_idx on public.app_devices (last_seen_at desc);
create index if not exists admin_audit_log_created_at_idx on public.admin_audit_log (created_at desc);

alter table public.scan_events enable row level security;
alter table public.scan_feedback enable row level security;
alter table public.url_reputation_cache enable row level security;
alter table public.app_devices enable row level security;
alter table public.admin_audit_log enable row level security;

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists set_url_reputation_cache_updated_at on public.url_reputation_cache;
create trigger set_url_reputation_cache_updated_at
before update on public.url_reputation_cache
for each row execute function public.set_updated_at();

