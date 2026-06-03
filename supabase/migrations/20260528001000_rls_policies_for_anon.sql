-- Community reports table
create table if not exists public.community_reports (
  id uuid primary key default gen_random_uuid(),
  hash text not null,
  risk_level text not null,
  family text,
  source text not null default 'ios',
  report_count integer not null default 1,
  first_reported_at timestamptz not null default now(),
  last_reported_at timestamptz not null default now()
);

create index if not exists community_reports_hash_idx on public.community_reports (hash);
create index if not exists community_reports_family_idx on public.community_reports (family);
create index if not exists community_reports_last_reported_idx on public.community_reports (last_reported_at desc);

-- Campaigns table
create table if not exists public.scam_campaigns (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  brand text not null,
  risk_level text not null default 'dangerous',
  region text,
  lat double precision,
  lon double precision,
  scan_count integer not null default 0,
  first_seen timestamptz not null default now(),
  last_seen timestamptz not null default now(),
  status text not null default 'activă',
  description text not null default '',
  safe_action text not null default '',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists scam_campaigns_status_idx on public.scam_campaigns (status);
create index if not exists scam_campaigns_last_seen_idx on public.scam_campaigns (last_seen desc);

-- Push device tokens table
create table if not exists public.push_devices (
  id uuid primary key default gen_random_uuid(),
  token text not null unique,
  platform text not null default 'ios',
  locale text not null default 'ro-RO',
  created_at timestamptz not null default now(),
  last_seen_at timestamptz not null default now()
);

create index if not exists push_devices_token_idx on public.push_devices (token);
create index if not exists push_devices_last_seen_idx on public.push_devices (last_seen_at desc);

-- RLS policies for community_reports
alter table public.community_reports enable row level security;
create policy "anon_insert_community_reports"
  on public.community_reports for insert to anon with check (true);
create policy "anon_select_community_reports"
  on public.community_reports for select to anon using (true);

-- RLS policies for scam_campaigns
alter table public.scam_campaigns enable row level security;
create policy "anon_select_scam_campaigns"
  on public.scam_campaigns for select to anon using (true);

-- RLS policies for push_devices
alter table public.push_devices enable row level security;
create policy "anon_insert_push_devices"
  on public.push_devices for insert to anon with check (true);
create policy "anon_update_push_devices"
  on public.push_devices for update to anon using (true);

-- Allow anon key to INSERT into scan_events
create policy "anon_insert_scan_events"
  on public.scan_events
  for insert
  to anon
  with check (true);

-- Allow anon key to SELECT from scan_events
create policy "anon_select_scan_events"
  on public.scan_events
  for select
  to anon
  using (true);

-- Allow anon key to INSERT into scan_feedback
create policy "anon_insert_scan_feedback"
  on public.scan_feedback
  for insert
  to anon
  with check (true);

-- Allow anon key to SELECT from scan_feedback
create policy "anon_select_scan_feedback"
  on public.scan_feedback
  for select
  to anon
  using (true);

-- Allow anon key to INSERT into url_reputation_cache (with upsert)
create policy "anon_insert_url_reputation_cache"
  on public.url_reputation_cache
  for insert
  to anon
  with check (true);

-- Allow anon key to UPDATE url_reputation_cache (for upsert merges)
create policy "anon_update_url_reputation_cache"
  on public.url_reputation_cache
  for update
  to anon
  using (true);

-- Allow anon key to SELECT from url_reputation_cache
create policy "anon_select_url_reputation_cache"
  on public.url_reputation_cache
  for select
  to anon
  using (true);

-- Allow anon key to INSERT into app_devices
create policy "anon_insert_app_devices"
  on public.app_devices
  for insert
  to anon
  with check (true);

-- Allow anon key to SELECT from app_devices
create policy "anon_select_app_devices"
  on public.app_devices
  for select
  to anon
  using (true);
