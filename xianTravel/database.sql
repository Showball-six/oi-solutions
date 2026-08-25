-- 西安之行 · Supabase 数据库初始化
-- 在 Supabase Dashboard -> SQL Editor 中一次性运行此文件。
-- 可重复运行大部分语句；如果你修改过同名对象，请先检查差异。

create schema if not exists private;

-- private schema 仅允许已认证用户通过指定 helper functions 使用。
revoke all on schema private from public;
grant usage on schema private to authenticated;

-- =========================================================
-- 1. Tables
-- =========================================================

create table if not exists public.trips (
  id uuid primary key default gen_random_uuid(),
  name text not null default '西安之行',
  start_date date not null,
  end_date date not null,
  owner_id uuid not null references auth.users(id) on delete cascade,
  join_code text not null unique default upper(substr(replace(gen_random_uuid()::text, '-', ''), 1, 8)),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint trips_date_order check (end_date >= start_date)
);

create table if not exists public.trip_members (
  trip_id uuid not null references public.trips(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  role text not null default 'member' check (role in ('owner', 'member')),
  created_at timestamptz not null default now(),
  primary key (trip_id, user_id)
);

create index if not exists trip_members_user_id_idx
  on public.trip_members(user_id);

create table if not exists public.schedule_items (
  id uuid primary key default gen_random_uuid(),
  trip_id uuid not null references public.trips(id) on delete cascade,
  day date not null,
  start_time time not null,
  duration_minutes integer not null default 60
    check (duration_minutes between 15 and 960),
  title text not null,
  note text not null default '',
  type text not null default 'normal'
    check (type in ('normal', 'food')),
  priority boolean not null default false,
  tags text[] not null default '{}',
  created_by uuid not null references auth.users(id) on delete cascade,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists schedule_items_trip_day_time_idx
  on public.schedule_items(trip_id, day, start_time);

create table if not exists public.reservations (
  id uuid primary key default gen_random_uuid(),
  trip_id uuid not null references public.trips(id) on delete cascade,
  name text not null,
  status text not null default 'todo'
    check (status in ('todo', 'watch', 'done')),
  visit_date text not null default '',
  deadline text not null default '',
  method text not null default '',
  note text not null default '',
  created_by uuid not null references auth.users(id) on delete cascade,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists reservations_trip_idx
  on public.reservations(trip_id);

create table if not exists public.foods (
  id uuid primary key default gen_random_uuid(),
  trip_id uuid not null references public.trips(id) on delete cascade,
  name text not null,
  category text not null default '其他',
  default_time time not null default '12:00',
  duration_minutes integer not null default 60
    check (duration_minutes between 15 and 300),
  note text not null default '',
  created_by uuid not null references auth.users(id) on delete cascade,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists foods_trip_category_idx
  on public.foods(trip_id, category);

-- =========================================================
-- 2. Helper functions
-- =========================================================

create or replace function private.is_trip_member(p_trip_id uuid)
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
  select exists (
    select 1
    from public.trip_members tm
    where tm.trip_id = p_trip_id
      and tm.user_id = (select auth.uid())
  );
$$;

create or replace function private.is_trip_owner(p_trip_id uuid)
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
  select exists (
    select 1
    from public.trips t
    where t.id = p_trip_id
      and t.owner_id = (select auth.uid())
  );
$$;

create or replace function private.add_trip_owner_member()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  insert into public.trip_members (trip_id, user_id, role)
  values (new.id, new.owner_id, 'owner')
  on conflict (trip_id, user_id) do nothing;
  return new;
end;
$$;

drop trigger if exists trips_add_owner_member on public.trips;
create trigger trips_add_owner_member
after insert on public.trips
for each row execute function private.add_trip_owner_member();

create or replace function private.set_updated_at()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists trips_set_updated_at on public.trips;
create trigger trips_set_updated_at
before update on public.trips
for each row execute function private.set_updated_at();

drop trigger if exists schedule_items_set_updated_at on public.schedule_items;
create trigger schedule_items_set_updated_at
before update on public.schedule_items
for each row execute function private.set_updated_at();

drop trigger if exists reservations_set_updated_at on public.reservations;
create trigger reservations_set_updated_at
before update on public.reservations
for each row execute function private.set_updated_at();

drop trigger if exists foods_set_updated_at on public.foods;
create trigger foods_set_updated_at
before update on public.foods
for each row execute function private.set_updated_at();

-- 使用 8 位共享码加入旅行。只有已登录用户可调用。
create or replace function public.join_trip_by_code(p_code text)
returns uuid
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_trip_id uuid;
  v_uid uuid;
begin
  v_uid := (select auth.uid());
  if v_uid is null then
    raise exception 'Authentication required';
  end if;

  select t.id
    into v_trip_id
  from public.trips t
  where upper(t.join_code) = upper(trim(p_code))
  limit 1;

  if v_trip_id is null then
    raise exception 'Invalid join code';
  end if;

  insert into public.trip_members (trip_id, user_id, role)
  values (v_trip_id, v_uid, 'member')
  on conflict (trip_id, user_id) do nothing;

  return v_trip_id;
end;
$$;

revoke all on function public.join_trip_by_code(text) from public, anon;
grant execute on function public.join_trip_by_code(text) to authenticated;

-- =========================================================
-- 3. Row Level Security
-- =========================================================

alter table public.trips enable row level security;
alter table public.trip_members enable row level security;
alter table public.schedule_items enable row level security;
alter table public.reservations enable row level security;
alter table public.foods enable row level security;

-- 明确控制 Data API 权限
revoke all on table public.trips from anon, authenticated;
revoke all on table public.trip_members from anon, authenticated;
revoke all on table public.schedule_items from anon, authenticated;
revoke all on table public.reservations from anon, authenticated;
revoke all on table public.foods from anon, authenticated;

grant select, insert, update, delete on table public.trips to authenticated;
grant select on table public.trip_members to authenticated;
grant select, insert, update, delete on table public.schedule_items to authenticated;
grant select, insert, update, delete on table public.reservations to authenticated;
grant select, insert, update, delete on table public.foods to authenticated;

-- trips
drop policy if exists "trips_select_members" on public.trips;
create policy "trips_select_members"
on public.trips for select
to authenticated
using ((select private.is_trip_member(id)));

drop policy if exists "trips_insert_owner" on public.trips;
create policy "trips_insert_owner"
on public.trips for insert
to authenticated
with check (
  (select auth.uid()) is not null
  and owner_id = (select auth.uid())
);

drop policy if exists "trips_update_owner" on public.trips;
create policy "trips_update_owner"
on public.trips for update
to authenticated
using ((select private.is_trip_owner(id)))
with check (owner_id = (select auth.uid()));

drop policy if exists "trips_delete_owner" on public.trips;
create policy "trips_delete_owner"
on public.trips for delete
to authenticated
using ((select private.is_trip_owner(id)));

-- trip_members：成员可查看同一旅行里的成员名单；加入通过 RPC 完成。
drop policy if exists "trip_members_select_members" on public.trip_members;
create policy "trip_members_select_members"
on public.trip_members for select
to authenticated
using ((select private.is_trip_member(trip_id)));

-- schedule_items
drop policy if exists "schedule_select_members" on public.schedule_items;
create policy "schedule_select_members"
on public.schedule_items for select
to authenticated
using ((select private.is_trip_member(trip_id)));

drop policy if exists "schedule_insert_members" on public.schedule_items;
create policy "schedule_insert_members"
on public.schedule_items for insert
to authenticated
with check (
  (select private.is_trip_member(trip_id))
  and created_by = (select auth.uid())
);

drop policy if exists "schedule_update_members" on public.schedule_items;
create policy "schedule_update_members"
on public.schedule_items for update
to authenticated
using ((select private.is_trip_member(trip_id)))
with check ((select private.is_trip_member(trip_id)));

drop policy if exists "schedule_delete_members" on public.schedule_items;
create policy "schedule_delete_members"
on public.schedule_items for delete
to authenticated
using ((select private.is_trip_member(trip_id)));

-- reservations
drop policy if exists "reservations_select_members" on public.reservations;
create policy "reservations_select_members"
on public.reservations for select
to authenticated
using ((select private.is_trip_member(trip_id)));

drop policy if exists "reservations_insert_members" on public.reservations;
create policy "reservations_insert_members"
on public.reservations for insert
to authenticated
with check (
  (select private.is_trip_member(trip_id))
  and created_by = (select auth.uid())
);

drop policy if exists "reservations_update_members" on public.reservations;
create policy "reservations_update_members"
on public.reservations for update
to authenticated
using ((select private.is_trip_member(trip_id)))
with check ((select private.is_trip_member(trip_id)));

drop policy if exists "reservations_delete_members" on public.reservations;
create policy "reservations_delete_members"
on public.reservations for delete
to authenticated
using ((select private.is_trip_member(trip_id)));

-- foods
drop policy if exists "foods_select_members" on public.foods;
create policy "foods_select_members"
on public.foods for select
to authenticated
using ((select private.is_trip_member(trip_id)));

drop policy if exists "foods_insert_members" on public.foods;
create policy "foods_insert_members"
on public.foods for insert
to authenticated
with check (
  (select private.is_trip_member(trip_id))
  and created_by = (select auth.uid())
);

drop policy if exists "foods_update_members" on public.foods;
create policy "foods_update_members"
on public.foods for update
to authenticated
using ((select private.is_trip_member(trip_id)))
with check ((select private.is_trip_member(trip_id)));

drop policy if exists "foods_delete_members" on public.foods;
create policy "foods_delete_members"
on public.foods for delete
to authenticated
using ((select private.is_trip_member(trip_id)));

-- helper schema functions only for authenticated users
revoke all on function private.is_trip_member(uuid) from public, anon;
revoke all on function private.is_trip_owner(uuid) from public, anon;
grant execute on function private.is_trip_member(uuid) to authenticated;
grant execute on function private.is_trip_owner(uuid) to authenticated;

-- =========================================================
-- 4. Realtime
-- =========================================================
-- Postgres Changes 对这个两人旅行应用足够简单。
-- DELETE 事件需要 full replica identity 才能携带完整旧行。

alter table public.schedule_items replica identity full;
alter table public.reservations replica identity full;
alter table public.foods replica identity full;

do $$
begin
  if not exists (
    select 1 from pg_publication_tables
    where pubname = 'supabase_realtime'
      and schemaname = 'public'
      and tablename = 'schedule_items'
  ) then
    execute 'alter publication supabase_realtime add table public.schedule_items';
  end if;

  if not exists (
    select 1 from pg_publication_tables
    where pubname = 'supabase_realtime'
      and schemaname = 'public'
      and tablename = 'reservations'
  ) then
    execute 'alter publication supabase_realtime add table public.reservations';
  end if;

  if not exists (
    select 1 from pg_publication_tables
    where pubname = 'supabase_realtime'
      and schemaname = 'public'
      and tablename = 'foods'
  ) then
    execute 'alter publication supabase_realtime add table public.foods';
  end if;
end $$;
