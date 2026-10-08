-- One row per account holding that person's bookmarks, notes, reading
-- place and settings (a single JSON document the app merges on each sync).
-- Run this once in your Supabase project: SQL Editor -> New query -> Run.

create table if not exists public.reader_data (
  user_id uuid primary key default auth.uid() references auth.users (id) on delete cascade,
  data jsonb not null default '{}'::jsonb,
  updated_at timestamptz not null default now(),
  constraint reader_data_size check (octet_length(data::text) < 2000000)
);

-- Row Level Security: each signed-in person can only ever see and change
-- their own row. Nobody (not even signed-in users) can read anyone else's.
alter table public.reader_data enable row level security;

drop policy if exists "Read own data" on public.reader_data;
create policy "Read own data" on public.reader_data
  for select to authenticated using ((select auth.uid()) = user_id);

drop policy if exists "Add own data" on public.reader_data;
create policy "Add own data" on public.reader_data
  for insert to authenticated with check ((select auth.uid()) = user_id);

drop policy if exists "Change own data" on public.reader_data;
create policy "Change own data" on public.reader_data
  for update to authenticated
  using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);

revoke all on public.reader_data from anon;
grant select, insert, update on public.reader_data to authenticated;

-- Lets a signed-in person delete their own account (and, through the
-- foreign key above, their saved data). It can only ever delete the caller.
create or replace function public.delete_my_account()
returns void
language plpgsql
security definer
set search_path = ''
as $$
begin
  if auth.uid() is null then
    raise exception 'not signed in';
  end if;
  delete from auth.users where id = auth.uid();
end;
$$;

revoke all on function public.delete_my_account() from public, anon;
grant execute on function public.delete_my_account() to authenticated;
