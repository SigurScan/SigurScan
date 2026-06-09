alter table public.fast_preview_cache
add column if not exists visual_only boolean not null default true;

alter table public.fast_preview_cache
add column if not exists verdict_role text not null default 'none';

-- Older worker versions persisted skipped/blocked targets, which may include
-- user-specific URLs. Remove them; alias rows are deleted through the FK.
delete from public.fast_preview_cache
where status in ('skipped', 'blocked');

alter table public.fast_preview_cache
drop constraint if exists fast_preview_cache_status_chk;

alter table public.fast_preview_cache
add constraint fast_preview_cache_status_chk
check (status in ('ready', 'dead', 'error'));

alter table public.fast_preview_cache
drop constraint if exists fast_preview_cache_visual_only_chk;

alter table public.fast_preview_cache
add constraint fast_preview_cache_visual_only_chk
check (visual_only is true and verdict_role = 'none');

comment on column public.fast_preview_cache.visual_only is
'Invariant: fast preview rows are UI-only and must never become verdict evidence.';

comment on column public.fast_preview_cache.verdict_role is
'Invariant: fast preview rows have no role in risk scoring or verdict generation.';
