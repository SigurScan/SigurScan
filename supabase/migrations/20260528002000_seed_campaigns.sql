-- Allow anon to insert scam_campaigns (for admin flows)
create policy "anon_insert_scam_campaigns"
  on public.scam_campaigns for insert to anon with check (true);

-- Seed sample campaigns
insert into public.scam_campaigns (title, brand, risk_level, region, lat, lon, scan_count, first_seen, last_seen, status, description, safe_action)
values
  ('SMS fals FAN Courier', 'FAN Courier', 'dangerous', 'București, Ilfov', 44.4268, 26.1025, 234, '2026-05-27T00:00:00+00:00', '2026-05-28T00:00:00+00:00', 'activă', 'SMS cu taxă de livrare 4.99 RON și link către fan-track-app[.]xyz. Furt cod WhatsApp.', 'Nu accesa linkul. Verifică AWB pe fancourier.ro.'),
  ('ANAF rambursare falsă', 'ANAF', 'dangerous', 'Național', 44.4268, 26.1025, 89, '2026-05-26T00:00:00+00:00', '2026-05-28T00:00:00+00:00', 'confirmată', 'Email cu "sold disponibil de rambursat" și link către anaf-gov[.]top.', 'Accesează SPV doar din aplicația oficială anaf.ro.'),
  ('WhatsApp code theft', 'WhatsApp', 'critical', 'Cluj, Timișoara', 46.7712, 23.6236, 156, '2026-05-27T00:00:00+00:00', '2026-05-28T00:00:00+00:00', 'activă', 'Mesaj de la "prieten" care cere codul de verificare WhatsApp. Conturi compromise în lanț.', 'Nu da codul. Sună persoana să confirmi. Activează 2FA.')
on conflict do nothing;
