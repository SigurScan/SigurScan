create table if not exists public.urlscan_preview_cache (
  url_hash text primary key,
  canonical_url text,
  final_url text not null,
  final_registered_domain text,
  uuid text,
  report_url text,
  screenshot_url text,
  verdict text,
  severity text,
  details text,
  score integer not null default 0,
  categories jsonb not null default '[]'::jsonb,
  brands jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  expires_at timestamptz
);

create index if not exists urlscan_preview_cache_domain_idx
  on public.urlscan_preview_cache (final_registered_domain);

create index if not exists urlscan_preview_cache_expires_at_idx
  on public.urlscan_preview_cache (expires_at);

create index if not exists urlscan_preview_cache_updated_at_idx
  on public.urlscan_preview_cache (updated_at desc);

alter table public.urlscan_preview_cache enable row level security;

drop trigger if exists set_urlscan_preview_cache_updated_at on public.urlscan_preview_cache;
create trigger set_urlscan_preview_cache_updated_at
before update on public.urlscan_preview_cache
for each row execute function public.set_updated_at();

revoke all on table public.urlscan_preview_cache from anon;
revoke all on table public.urlscan_preview_cache from authenticated;
