-- v6 固定密码模式迁移
-- 运行前，请把下面的 xian2026 改成你自己的固定密码。
create extension if not exists pgcrypto with schema extensions;

alter table public.trips alter column owner_id drop not null;
alter table public.trips add column if not exists password_hash text;
alter table public.schedule_items alter column created_by drop not null;
alter table public.reservations alter column created_by drop not null;
alter table public.foods alter column created_by drop not null;

create or replace function private.add_trip_owner_member()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  if new.owner_id is not null then
    insert into public.trip_members (trip_id,user_id,role)
    values (new.id,new.owner_id,'owner')
    on conflict (trip_id,user_id) do nothing;
  end if;
  return new;
end;
$$;

insert into public.trips
(id,name,start_date,end_date,owner_id,join_code,password_hash)
values
('8b92740d-1b91-4cf7-9c2a-202609040909','西安之行','2026-09-04','2026-09-09',null,'XIAN2026',
 extensions.crypt('xian2026', extensions.gen_salt('bf'))) -- <<< 修改这里的 xian2026
on conflict (id) do update set
  name=excluded.name,
  start_date=excluded.start_date,
  end_date=excluded.end_date,
  password_hash=excluded.password_hash,
  updated_at=now();

create or replace function public.unlock_trip_by_password(p_password text)
returns uuid
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_uid uuid;
  v_trip_id uuid;
begin
  v_uid := (select auth.uid());
  if v_uid is null then raise exception 'Authentication required'; end if;

  select id into v_trip_id
  from public.trips
  where id='8b92740d-1b91-4cf7-9c2a-202609040909'
    and password_hash = extensions.crypt(p_password, password_hash);

  if v_trip_id is null then raise exception 'Invalid trip password'; end if;

  insert into public.trip_members(trip_id,user_id,role)
  values(v_trip_id,v_uid,'member')
  on conflict(trip_id,user_id) do nothing;

  return v_trip_id;
end;
$$;

revoke all on function public.unlock_trip_by_password(text) from public, anon;
grant execute on function public.unlock_trip_by_password(text) to authenticated;

-- 初始化模板（仅当对应表尚无这趟旅行的数据）
insert into public.schedule_items
(trip_id,day,start_time,duration_minutes,title,note,type,priority,tags,created_by)
select '8b92740d-1b91-4cf7-9c2a-202609040909',v.day::date,v.start_time::time,v.duration_minutes,v.title,v.note,v.type,v.priority,v.tags,null
from (values
 ('2026-09-05','10:30',90,'睡到自然醒 · 早餐 · 出发','凌晨抵达，第一天不安排必须早起的项目。','normal',false,array['轻松开局']::text[]),
 ('2026-09-05','14:00',210,'西安市区慢游','城墙、钟鼓楼、街区夜游按体力灵活组合。','normal',false,array['市区','机动']::text[]),
 ('2026-09-06','09:00',180,'陕西历史博物馆','当前首选日；若确定 9/6，9/1 17:00 抢票。','normal',true,array['S级预约']::text[]),
 ('2026-09-06','18:30',180,'大雁塔 · 大唐不夜城','与陕历博地理位置较顺，安排晚间游览。','normal',false,array['夜游']::text[]),
 ('2026-09-07','08:30',810,'兵马俑 → 华清宫 →《长恨歌》','周一优先安排临潼线。','normal',true,array['临潼','重点日']::text[]),
 ('2026-09-08','09:30',360,'碑林 · 书院门 · 城墙','市区文化线候选。','normal',false,array['市区文化']::text[])
) v(day,start_time,duration_minutes,title,note,type,priority,tags)
where not exists(select 1 from public.schedule_items where trip_id='8b92740d-1b91-4cf7-9c2a-202609040909');

insert into public.reservations
(trip_id,name,status,visit_date,deadline,method,note,created_by)
select '8b92740d-1b91-4cf7-9c2a-202609040909',v.name,v.status,v.visit_date,v.deadline,v.method,v.note,null
from (values
 ('陕西历史博物馆','todo','9月6日（候选）','9月1日 17:00','官方微信公众号','建议提前预填两人实名信息。'),
 ('秦始皇帝陵博物院 / 兵马俑','watch','9月7日（候选）','确定临潼日后尽早购买','官方渠道','兵马俑 + 丽山园建议整体预留至少半天。'),
 ('《长恨歌》','watch','9月7日（候选）','临近出发前核当期放票时间','华清宫官方渠道','与兵马俑、华清宫同日。')
) v(name,status,visit_date,deadline,method,note)
where not exists(select 1 from public.reservations where trip_id='8b92740d-1b91-4cf7-9c2a-202609040909');

insert into public.foods
(trip_id,name,category,default_time,duration_minutes,note,created_by)
select '8b92740d-1b91-4cf7-9c2a-202609040909',v.name,v.category,v.default_time::time,v.duration_minutes,v.note,null
from (values
 ('肉夹馍','小吃','10:00',45,'经典必吃'),
 ('凉皮','小吃','15:30',45,'清爽开胃'),
 ('羊肉泡馍','正餐','12:30',90,'建议留足时间'),
 ('葫芦鸡','正餐','18:30',90,'陕西传统名菜'),
 ('biangbiang面','面食','12:00',60,'宽面代表'),
 ('油泼面','面食','12:00',60,'香辣'),
 ('甑糕','甜品','09:30',30,'糯米红枣甜香'),
 ('镜糕','甜品','15:00',30,'边走边吃'),
 ('涮牛肚','夜宵','21:30',75,'麻酱香'),
 ('烤肉','夜宵','21:30',90,'适合夜游后'),
 ('酸梅汤','饮品','16:00',30,'解腻'),
 ('冰峰汽水','饮品','13:30',15,'西安经典搭配')
) v(name,category,default_time,duration_minutes,note)
where not exists(select 1 from public.foods where trip_id='8b92740d-1b91-4cf7-9c2a-202609040909');

select 'v6 password mode ready' as status;


-- =========================================================
-- 验证 pgcrypto 与密码哈希是否正常
-- =========================================================
select
  n.nspname as schema_name,
  p.proname as function_name
from pg_proc p
join pg_namespace n on n.oid = p.pronamespace
where p.proname in ('crypt','gen_salt')
order by p.proname;

select
  id,
  name,
  password_hash is not null as has_password
from public.trips
where id = '8b92740d-1b91-4cf7-9c2a-202609040909';
