-- Shared monthly budgets for scarce/paid providers.
-- Cloud Run can run multiple instances, so local counters are not enough.

create table if not exists public.provider_monthly_budget_usage (
  provider text not null,
  month_key text not null check (month_key ~ '^[0-9]{4}-[0-9]{2}$'),
  used_count integer not null default 0 check (used_count >= 0),
  monthly_limit integer not null check (monthly_limit >= 0),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (provider, month_key)
);

alter table public.provider_monthly_budget_usage enable row level security;

create or replace function public.try_consume_provider_budget(
  p_provider text,
  p_month_key text,
  p_monthly_limit integer
)
returns boolean
language plpgsql
security definer
set search_path = public
as $$
declare
  consumed_count integer;
begin
  if nullif(btrim(p_provider), '') is null
     or nullif(btrim(p_month_key), '') is null
     or p_monthly_limit is null
     or p_monthly_limit <= 0 then
    return false;
  end if;

  loop
    update public.provider_monthly_budget_usage
       set used_count = used_count + 1,
           monthly_limit = p_monthly_limit,
           updated_at = now()
     where provider = btrim(lower(p_provider))
       and month_key = btrim(p_month_key)
       and used_count < p_monthly_limit
     returning used_count into consumed_count;

    if found then
      return true;
    end if;

    begin
      insert into public.provider_monthly_budget_usage (
        provider,
        month_key,
        used_count,
        monthly_limit,
        created_at,
        updated_at
      )
      values (
        btrim(lower(p_provider)),
        btrim(p_month_key),
        1,
        p_monthly_limit,
        now(),
        now()
      );
      return true;
    exception when unique_violation then
      if exists (
        select 1
          from public.provider_monthly_budget_usage
         where provider = btrim(lower(p_provider))
           and month_key = btrim(p_month_key)
           and used_count >= p_monthly_limit
      ) then
        return false;
      end if;
    end;
  end loop;
end;
$$;

revoke all on function public.try_consume_provider_budget(text, text, integer) from public;
revoke all on function public.try_consume_provider_budget(text, text, integer) from anon;
revoke all on function public.try_consume_provider_budget(text, text, integer) from authenticated;
grant execute on function public.try_consume_provider_budget(text, text, integer) to service_role;
