-- v7：新增准备清单
create table if not exists public.preparation_items (
  id uuid primary key default gen_random_uuid(),
  trip_id uuid not null references public.trips(id) on delete cascade,
  name text not null,
  category text not null default '其他',
  note text not null default '',
  is_done boolean not null default false,
  created_by uuid references auth.users(id) on delete set null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists preparation_items_trip_done_idx
on public.preparation_items(trip_id, is_done, created_at);

alter table public.preparation_items enable row level security;

revoke all on table public.preparation_items from anon, authenticated;
grant select, insert, update, delete on table public.preparation_items to authenticated;

drop policy if exists "preparation_select_members" on public.preparation_items;
create policy "preparation_select_members"
on public.preparation_items for select to authenticated
using ((select private.is_trip_member(trip_id)));

drop policy if exists "preparation_insert_members" on public.preparation_items;
create policy "preparation_insert_members"
on public.preparation_items for insert to authenticated
with check (
  (select private.is_trip_member(trip_id))
  and (created_by is null or created_by = (select auth.uid()))
);

drop policy if exists "preparation_update_members" on public.preparation_items;
create policy "preparation_update_members"
on public.preparation_items for update to authenticated
using ((select private.is_trip_member(trip_id)))
with check ((select private.is_trip_member(trip_id)));

drop policy if exists "preparation_delete_members" on public.preparation_items;
create policy "preparation_delete_members"
on public.preparation_items for delete to authenticated
using ((select private.is_trip_member(trip_id)));

drop trigger if exists preparation_items_set_updated_at on public.preparation_items;
create trigger preparation_items_set_updated_at
before update on public.preparation_items
for each row execute function private.set_updated_at();

alter table public.preparation_items replica identity full;

do $$
begin
  if not exists (
    select 1 from pg_publication_tables
    where pubname='supabase_realtime'
      and schemaname='public'
      and tablename='preparation_items'
  ) then
    execute 'alter publication supabase_realtime add table public.preparation_items';
  end if;
end $$;

insert into public.preparation_items
(trip_id,name,category,note,is_done,created_by)
select '8b92740d-1b91-4cf7-9c2a-202609040909',v.name,v.category,v.note,false,null
from (values
 ('身份证','证件','两人都要带，出发前再确认一次'),
 ('充电宝','电子','提前充满电，注意航空携带规定'),
 ('充电器 / 数据线','电子','手机、手表、耳机等分别检查'),
 ('洗漱用品','日用','牙刷、牙膏、洁面、护肤等'),
 ('花露水','日用','户外和夜间备用'),
 ('防晒用品','日用','防晒霜、帽子或遮阳伞'),
 ('雨伞','日用','兼顾防晒和突发降雨'),
 ('常用药品','健康','肠胃药、创可贴等按需准备'),
 ('舒适步行鞋','衣物','西安日均步行量可能较大')
) as v(name,category,note)
where not exists (
  select 1 from public.preparation_items
  where trip_id='8b92740d-1b91-4cf7-9c2a-202609040909'
);

select 'preparation_items ready' as status;
