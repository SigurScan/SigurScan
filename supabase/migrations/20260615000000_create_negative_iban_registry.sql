-- Registru negativ de IBAN-uri raportate ca fraudă (catâri/complici).
-- Alimentat din alerte DNSC + rapoarte comunitare. Backend-ul scrie write-through
-- best-effort (services/negative_iban_registry.py + supabase_store.save_negative_iban).
create table if not exists public.negative_iban_registry (
  iban             text primary key,
  source           text not null default 'manual'
                   check (source in ('dnsc_alert','community_report','press','manual')),
  family           text,
  report_count     integer not null default 1 check (report_count >= 1),
  created_at       timestamptz not null default now(),
  last_reported_at timestamptz not null default now()
);

create index if not exists negative_iban_registry_source_idx on public.negative_iban_registry (source);

alter table public.negative_iban_registry enable row level security;
