-- Atomic VendorMemory write-through.
-- Service-role backend calls this RPC so repeat confirmations increment history
-- instead of overwriting seen_count back to 1.

create or replace function public.remember_vendor_iban(p_cui text, p_iban text)
returns void
language plpgsql
security definer
set search_path = public
as $$
begin
  if nullif(btrim(p_cui), '') is null or nullif(btrim(p_iban), '') is null then
    return;
  end if;

  insert into public.vendor_iban_memory (cui, iban, seen_count, first_seen_at, last_seen_at)
  values (btrim(p_cui), btrim(p_iban), 1, now(), now())
  on conflict (cui, iban) do update
    set seen_count = public.vendor_iban_memory.seen_count + 1,
        last_seen_at = now();
end;
$$;

revoke all on function public.remember_vendor_iban(text, text) from public;
revoke all on function public.remember_vendor_iban(text, text) from anon;
revoke all on function public.remember_vendor_iban(text, text) from authenticated;
grant execute on function public.remember_vendor_iban(text, text) to service_role;
