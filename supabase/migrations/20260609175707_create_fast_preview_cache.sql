create table if not exists public.fast_preview_cache (
  url_hash text primary key,
  original_url text,
  final_url text not null,
  final_domain text not null,
  screenshot_path text,
  screenshot_w integer,
  screenshot_h integer,
  content_hash text,
  page_title text,
  http_status integer,
  redirect_chain jsonb not null default '[]'::jsonb,
  reachable boolean not null default false,
  status text not null default 'error',
  source text not null default 'precapture_worker',
  seed_category text,
  captured_at timestamptz not null default now(),
  expires_at timestamptz not null default now() + interval '7 days',
  source_email_id jsonb,
  error text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint fast_preview_cache_status_chk check (status in ('ready', 'dead', 'blocked', 'error', 'skipped'))
);

create index if not exists fast_preview_cache_expires_at_idx
  on public.fast_preview_cache (expires_at);

create index if not exists fast_preview_cache_final_domain_idx
  on public.fast_preview_cache (final_domain);

create index if not exists fast_preview_cache_seed_category_idx
  on public.fast_preview_cache (seed_category);

create index if not exists fast_preview_cache_status_idx
  on public.fast_preview_cache (status);

alter table public.fast_preview_cache enable row level security;

drop trigger if exists set_fast_preview_cache_updated_at on public.fast_preview_cache;
create trigger set_fast_preview_cache_updated_at
before update on public.fast_preview_cache
for each row execute function public.set_updated_at();

revoke all on table public.fast_preview_cache from anon;
revoke all on table public.fast_preview_cache from authenticated;

create table if not exists public.fast_preview_alias_cache (
  alias_hash text primary key,
  original_url text not null,
  final_url_hash text not null references public.fast_preview_cache(url_hash) on delete cascade,
  captured_at timestamptz not null default now(),
  expires_at timestamptz not null default now() + interval '7 days',
  created_at timestamptz not null default now()
);

create index if not exists fast_preview_alias_cache_final_url_hash_idx
  on public.fast_preview_alias_cache (final_url_hash);

create index if not exists fast_preview_alias_cache_expires_at_idx
  on public.fast_preview_alias_cache (expires_at);

alter table public.fast_preview_alias_cache enable row level security;

revoke all on table public.fast_preview_alias_cache from anon;
revoke all on table public.fast_preview_alias_cache from authenticated;

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('previews', 'previews', false, 5242880, array['image/png'])
on conflict (id) do update
set
  public = false,
  file_size_limit = excluded.file_size_limit,
  allowed_mime_types = excluded.allowed_mime_types;
