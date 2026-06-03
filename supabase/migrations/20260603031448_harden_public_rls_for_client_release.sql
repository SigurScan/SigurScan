-- Harden public RLS before mobile client release.
--
-- The Android/iOS clients must not read or write raw telemetry tables directly
-- with the public anon key. Clients call the NuDaClick backend, and the backend
-- uses server-side credentials plus rate limiting. The only public table data
-- left readable is validated campaign content intended for display.

-- community_reports: write/read only through backend.
drop policy if exists "anon_insert_community_reports" on public.community_reports;
drop policy if exists "anon_select_community_reports" on public.community_reports;
revoke all on table public.community_reports from anon;
revoke all on table public.community_reports from authenticated;

-- scam_campaigns: public read-only for active/confirmed campaign cards.
drop policy if exists "anon_select_scam_campaigns" on public.scam_campaigns;
drop policy if exists "anon_insert_scam_campaigns" on public.scam_campaigns;
revoke insert, update, delete on table public.scam_campaigns from anon;
revoke insert, update, delete on table public.scam_campaigns from authenticated;
grant select on table public.scam_campaigns to anon;
create policy "anon_select_public_scam_campaigns"
  on public.scam_campaigns
  for select
  to anon
  using (status in ('activă', 'confirmată', 'active', 'confirmed'));

-- push/app devices: no anonymous client-side registration in v1.
drop policy if exists "anon_insert_push_devices" on public.push_devices;
drop policy if exists "anon_update_push_devices" on public.push_devices;
revoke all on table public.push_devices from anon;
revoke all on table public.push_devices from authenticated;

drop policy if exists "anon_insert_app_devices" on public.app_devices;
drop policy if exists "anon_select_app_devices" on public.app_devices;
revoke all on table public.app_devices from anon;
revoke all on table public.app_devices from authenticated;

-- scan telemetry and feedback: backend-only.
drop policy if exists "anon_insert_scan_events" on public.scan_events;
drop policy if exists "anon_select_scan_events" on public.scan_events;
revoke all on table public.scan_events from anon;
revoke all on table public.scan_events from authenticated;

drop policy if exists "anon_insert_scan_feedback" on public.scan_feedback;
drop policy if exists "anon_select_scan_feedback" on public.scan_feedback;
revoke all on table public.scan_feedback from anon;
revoke all on table public.scan_feedback from authenticated;

-- reputation cache can reveal provider results and scanned targets; backend-only.
drop policy if exists "anon_insert_url_reputation_cache" on public.url_reputation_cache;
drop policy if exists "anon_update_url_reputation_cache" on public.url_reputation_cache;
drop policy if exists "anon_select_url_reputation_cache" on public.url_reputation_cache;
revoke all on table public.url_reputation_cache from anon;
revoke all on table public.url_reputation_cache from authenticated;
