alter table public.fast_preview_cache
drop constraint if exists fast_preview_cache_status_chk;

alter table public.fast_preview_cache
add constraint fast_preview_cache_status_chk
check (status in ('ready', 'dead', 'blocked', 'error', 'skipped'));
