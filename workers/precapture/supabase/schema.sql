-- Reference schema only. In the SigurScan repo, the production migration lives in:
-- ../../supabase/migrations/*_create_fast_preview_cache.sql

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
  visual_only boolean not null default true,
  verdict_role text not null default 'none',
  captured_at timestamptz not null default now(),
  expires_at timestamptz not null default now() + interval '7 days',
  source_email_id jsonb,
  error text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint fast_preview_cache_status_chk check (status in ('ready', 'dead', 'error')),
  constraint fast_preview_cache_visual_only_chk check (visual_only is true and verdict_role = 'none')
);

create table if not exists public.fast_preview_alias_cache (
  alias_hash text primary key,
  original_url text not null,
  final_url_hash text not null references public.fast_preview_cache(url_hash) on delete cascade,
  captured_at timestamptz not null default now(),
  expires_at timestamptz not null default now() + interval '7 days',
  created_at timestamptz not null default now()
);
