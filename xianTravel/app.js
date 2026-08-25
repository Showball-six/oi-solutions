import {createClient} from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.112.4/+esm';
import {SUPABASE_URL,SUPABASE_PUBLISHABLE_KEY} from './config.js';
const supabase=createClient(SUPABASE_URL,SUPABASE_PUBLISHABLE_KEY,{auth:{autoRefreshToken:true,persistSession:true,detectSessionInUrl:false}});
const TRIP='8b92740d-1b91-4cf7-9c2a-202609040909', UNLOCK='xian_unlock_v6', CACHE='xian_cache_v6';
const DAYS=[['2026-09-05','DAY 1','9月5日','周六'],['2026-09-06','DAY 2','9月6日','周日'],['2026-09-07','DAY 3','9月7日','周一'],['2026-09-08','DAY 4','9月8日','周二']].map(([id,label,date,weekday])=>({id,label,date,weekday}));
let user=null,schedule=[],reservations=[],foods=[],preparations=[],foodCat='全部',prepCat='全部',drag=null,channel=null,timer=null;
const $=id=>document.getElementById(id);
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const tm=t=>{const [h,m]=String(t||'00:00').slice(0,5).split(':').map(Number);return(h||0)*60+(m||0)};
const mt=m=>`${String(Math.floor(Math.max(0,Math.min(1439,m))/60)).padStart(2,'0')}:${String(Math.max(0,Math.min(1439,m))%60).padStart(2,'0')}`;
const dt=t=>String(t||'').slice(0,5), end=i=>mt(tm(i.start_time)+Number(i.duration_minutes||0));
function toast(s,e=false){const x=$('toast');x.textContent=s;x.className='toast show'+(e?' error':'');clearTimeout(timer);timer=setTimeout(()=>x.className='toast',3000)}
function sync(ok,s){const p=$('syncDot')?.parentElement;if(!p)return;p.classList.toggle('offline',!ok);$('syncText').textContent=s}
function showGate(){$('passwordScreen').classList.remove('hidden');$('app').classList.add('hidden');$('tripPassword').value=''}
function showApp(){$('passwordScreen').classList.add('hidden');$('app').classList.remove('hidden')}
function cache(){try{localStorage.setItem(CACHE,JSON.stringify({schedule,reservations,foods,preparations}))}catch{}}
function cached(){try{const d=JSON.parse(localStorage.getItem(CACHE)||'null');if(!d)return false;schedule=d.schedule||[];reservations=d.reservations||[];foods=d.foods||[];preparations=d.preparations||[];render();return true}catch{return false}}
function conflicts(){const m=new Map;for(const d of DAYS){const a=schedule.filter(x=>x.day===d.id).sort((x,y)=>tm(x.start_time)-tm(y.start_time));for(let i=0;i<a.length;i++)for(let j=i+1;j<a.length;j++){const x=a[i],y=a[j],xe=tm(x.start_time)+x.duration_minutes,ye=tm(y.start_time)+y.duration_minutes;if(tm(y.start_time)>=xe)break;if(tm(x.start_time)<ye&&tm(y.start_time)<xe){(m.get(x.id)||m.set(x.id,[]).get(x.id)).push(y.title);(m.get(y.id)||m.set(y.id,[]).get(y.id)).push(x.title)}}}return m}
function render(){renderR();renderP();renderB();renderF();cache()}
function renderR(){$('reservationGrid').innerHTML='';for(const r of reservations){const e=document.createElement('article'),st=r.status==='done'?'已预约':r.status==='todo'?'待预约':'待关注';e.className='reserve'+(r.status==='todo'?' hot':'');e.innerHTML=`<div class="reserve-top"><div class="reserve-name">${esc(r.name)}</div><span class="status ${r.status}">${st}</span></div><div class="reserve-info">${r.visit_date?`参观：${esc(r.visit_date)}<br>`:''}${r.deadline?`操作：${esc(r.deadline)}`:''}</div>${r.method?`<div class="reserve-method">${esc(r.method)}</div>`:''}<div class="reserve-actions"><button class="tiny edit">编辑</button><button class="tiny del">删除</button></div>`;e.querySelector('.edit').onclick=()=>openR(r.id);e.querySelector('.del').onclick=()=>del('reservations',r.id,r.name);$('reservationGrid').appendChild(e)}if(!reservations.length)$('reservationGrid').innerHTML='<div class="empty">暂无预约项目</div>'}
function renderP(){
  const grid=$('preparationGrid'),filters=$('prepFilters');if(!grid||!filters)return;
  const cats=['全部',...new Set(preparations.map(x=>x.category||'其他'))];if(!cats.includes(prepCat))prepCat='全部';
  filters.innerHTML='';
  for(const c of cats){const b=document.createElement('button');b.type='button';b.className='filter'+(c===prepCat?' active':'');b.textContent=c;b.onclick=()=>{prepCat=c;renderP()};filters.appendChild(b)}
  const done=preparations.filter(x=>x.is_done).length,total=preparations.length;
  $('prepProgressText').textContent=`${done} / ${total} 已准备`;$('prepProgressBar').style.width=total?`${Math.round(done/total*100)}%`:'0%';
  grid.innerHTML='';
  const items=preparations.filter(x=>prepCat==='全部'||x.category===prepCat).slice().sort((a,b)=>Number(a.is_done)-Number(b.is_done)||String(a.category).localeCompare(String(b.category))||String(a.name).localeCompare(String(b.name)));
  for(const p of items){const e=document.createElement('article');e.className='prep-item'+(p.is_done?' done':'');e.innerHTML=`<input class="prep-checkbox" type="checkbox" ${p.is_done?'checked':''}><div class="prep-body"><div class="prep-top"><div class="prep-name">${esc(p.name)}</div><span class="prep-category">${esc(p.category||'其他')}</span></div>${p.note?`<div class="prep-note">${esc(p.note)}</div>`:''}<div class="prep-actions"><button class="edit" type="button">编辑</button><button class="del" type="button">删除</button></div></div>`;
    e.querySelector('.prep-checkbox').onchange=async ev=>{const next=ev.target.checked;const {error}=await supabase.from('preparation_items').update({is_done:next}).eq('id',p.id).eq('trip_id',TRIP);if(error){ev.target.checked=!next;return toast(error.message,true)}p.is_done=next;renderP();cache();toast(next?`已准备：${p.name}`:`已取消：${p.name}`)};
    e.querySelector('.edit').onclick=()=>openP(p.id);e.querySelector('.del').onclick=()=>del('preparation_items',p.id,p.name);grid.appendChild(e)}
  if(!items.length)grid.innerHTML='<div class="empty">当前分类暂无准备项</div>'
}
function renderB(){const cm=conflicts();$('board').innerHTML='';for(const d of DAYS){const a=schedule.filter(x=>x.day===d.id).sort((x,y)=>tm(x.start_time)-tm(y.start_time)),bad=a.some(x=>cm.has(x.id)),s=document.createElement('section');s.className='day'+(bad?' has-conflict':'');s.dataset.day=d.id;s.innerHTML=`<header class="day-head"><div class="day-kicker">${d.label}</div><div class="day-line"><strong>${d.date}</strong><span>${d.weekday}</span></div><div class="day-conflict">⚠ 存在时间冲突，请调整时间</div></header><div class="cards"></div>`;const h=s.querySelector('.cards');if(!a.length)h.innerHTML='<div class="empty">暂无安排<br>把日程或美食拖到这里</div>';for(const i of a){const names=cm.get(i.id)||[],e=document.createElement('article');e.draggable=true;e.dataset.id=i.id;e.className='card'+(i.priority?' priority':'')+(i.type==='food'?' food':'')+(names.length?' conflict':'');e.innerHTML=`<div class="card-top"><span class="time">${dt(i.start_time)}–${end(i)}</span><span class="kind"></span></div><div class="card-title">${esc(i.title)}</div>${i.note?`<div class="card-note">${esc(i.note)}</div>`:''}${names.length?`<div class="conflict-note">⚠ 与 ${esc(names.join('、'))} 时间重叠</div>`:''}<div class="card-actions"><select>${DAYS.map(x=>`<option value="${x.id}" ${x.id===i.day?'selected':''}>${x.date}</option>`).join('')}</select><button class="edit">编辑</button><button class="del">删除</button></div>`;e.querySelector('select').onchange=x=>move(i,x.target.value);e.querySelector('.edit').onclick=()=>openS(i.id);e.querySelector('.del').onclick=()=>del('schedule_items',i.id,i.title);h.appendChild(e)}$('board').appendChild(s)}bindDrag()}
function renderF(){const cats=['全部',...new Set(foods.map(f=>f.category))];if(!cats.includes(foodCat))foodCat='全部';$('foodFilters').innerHTML='';for(const c of cats){const b=document.createElement('button');b.className='filter'+(c===foodCat?' active':'');b.textContent=c;b.onclick=()=>{foodCat=c;renderF()};$('foodFilters').appendChild(b)}$('foodList').innerHTML='';for(const f of foods.filter(x=>foodCat==='全部'||x.category===foodCat)){const e=document.createElement('article');e.className='food-item';e.draggable=true;e.dataset.food=f.id;e.innerHTML=`<div class="food-name">${esc(f.name)}</div><div class="food-cat">${esc(f.category)} · ${esc(f.note||'')}</div><div class="food-default">默认 ${dt(f.default_time)} · ${f.duration_minutes} 分钟</div><div class="food-actions"><select>${DAYS.map(d=>`<option value="${d.id}">${d.date}</option>`).join('')}</select><button class="join">加入</button><button class="edit">编辑</button><button class="del">删除</button></div>`;e.ondragstart=()=>{drag={type:'food',id:f.id}};e.ondragend=()=>drag=null;e.querySelector('.join').onclick=()=>addFood(f.id,e.querySelector('select').value);e.querySelector('.edit').onclick=()=>openF(f.id);e.querySelector('.del').onclick=()=>del('foods',f.id,f.name);$('foodList').appendChild(e)}}
function bindDrag(){document.querySelectorAll('.card').forEach(e=>{e.ondragstart=()=>drag={type:'schedule',id:e.dataset.id};e.ondragend=()=>drag=null});document.querySelectorAll('.day').forEach(d=>{d.ondragover=e=>{e.preventDefault();d.classList.add('dragover')};d.ondragleave=e=>{if(!d.contains(e.relatedTarget))d.classList.remove('dragover')};d.ondrop=async e=>{e.preventDefault();d.classList.remove('dragover');if(!drag)return;if(drag.type==='schedule'){const i=schedule.find(x=>x.id===drag.id);if(i)await move(i,d.dataset.day)}else await addFood(drag.id,d.dataset.day);drag=null}})}
async function anon(){
  const {data:{session},error:sessionError}=await supabase.auth.getSession();
  if(sessionError) throw sessionError;

  if(session?.user){
    user=session.user;
    return;
  }

  const {data,error}=await supabase.auth.signInAnonymously();
  if(error){
    throw new Error('Anonymous Sign-In 失败：'+(error.message||String(error)));
  }

  if(!data?.user){
    throw new Error('Anonymous Sign-In 未返回用户对象');
  }

  user=data.user;
}
async function member(){const {data,error}=await supabase.from('trips').select('id').eq('id',TRIP).maybeSingle();if(error)throw error;return !!data}
async function load(){sync(true,'正在同步…');const [s,r,f,p]=await Promise.all([supabase.from('schedule_items').select('*').eq('trip_id',TRIP).order('day').order('start_time'),supabase.from('reservations').select('*').eq('trip_id',TRIP).order('created_at'),supabase.from('foods').select('*').eq('trip_id',TRIP).order('category'),supabase.from('preparation_items').select('*').eq('trip_id',TRIP).order('created_at')]);const er=s.error||r.error||f.error||p.error;if(er)throw er;schedule=s.data||[];reservations=r.data||[];foods=f.data||[];preparations=p.data||[];render();sync(true,'云端已同步')}
async function sub(){if(channel)await supabase.removeChannel(channel);channel=supabase.channel('xian-v6').on('postgres_changes',{event:'*',schema:'public',table:'schedule_items',filter:`trip_id=eq.${TRIP}`},()=>load()).on('postgres_changes',{event:'*',schema:'public',table:'reservations',filter:`trip_id=eq.${TRIP}`},()=>load()).on('postgres_changes',{event:'*',schema:'public',table:'foods',filter:`trip_id=eq.${TRIP}`},()=>load()).on('postgres_changes',{event:'*',schema:'public',table:'preparation_items',filter:`trip_id=eq.${TRIP}`},()=>load()).subscribe()}
async function boot(){try{await anon();if(!(await member())||sessionStorage.getItem(UNLOCK)!=='1'){showGate();return}showApp();try{await load()}catch(e){if(!cached())throw e;sync(false,'网络异常 · 已载入缓存')}await sub()}catch(e){console.error(e);toast('初始化失败：'+e.message,true);showGate()}}
async function move(i,day){const old=i.day;i.day=day;renderB();const {error}=await supabase.from('schedule_items').update({day}).eq('id',i.id).eq('trip_id',TRIP);if(error){i.day=old;renderB();return toast(error.message,true)}await load()}
async function addFood(id,day){const f=foods.find(x=>x.id===id);if(!f)return;const {error}=await supabase.from('schedule_items').insert({trip_id:TRIP,day,start_time:dt(f.default_time),duration_minutes:f.duration_minutes,title:f.name,note:f.note||'',type:'food',priority:false,tags:['美食',f.category],created_by:user.id});if(error)return toast(error.message,true);await load()}
async function del(table,id,name){if(!confirm(`删除“${name}”？`))return;const {error}=await supabase.from(table).delete().eq('id',id).eq('trip_id',TRIP);if(error)return toast(error.message,true);await load()}
function open(id){$(id).classList.add('open')}function close(id){$(id).classList.remove('open')}
function openR(id){const r=reservations.find(x=>x.id===id);$('reservationId').value=r?.id||'';$('reservationName').value=r?.name||'';$('reservationStatus').value=r?.status||'todo';$('reservationVisit').value=r?.visit_date||'';$('reservationDeadline').value=r?.deadline||'';$('reservationMethod').value=r?.method||'';$('reservationNote').value=r?.note||'';$('reservationModalTitle').textContent=r?'编辑预约':'新增预约';open('reservationModal')}
function openS(id){const s=schedule.find(x=>x.id===id);$('scheduleId').value=s?.id||'';$('scheduleDay').value=s?.day||DAYS[0].id;$('scheduleStart').value=dt(s?.start_time||'10:00');$('scheduleDuration').value=s?.duration_minutes||60;$('scheduleType').value=s?.type||'normal';$('scheduleTitle').value=s?.title||'';$('scheduleNote').value=s?.note||'';$('scheduleModalTitle').textContent=s?'编辑日程':'新增日程';open('scheduleModal')}
function openP(id){const p=preparations.find(x=>x.id===id);$('preparationId').value=p?.id||'';$('preparationName').value=p?.name||'';$('preparationCategory').value=p?.category||'其他';$('preparationNote').value=p?.note||'';$('preparationDone').checked=!!p?.is_done;$('preparationModalTitle').textContent=p?'编辑准备物品':'新增准备物品';open('preparationModal')}
function openF(id){const f=foods.find(x=>x.id===id);$('foodId').value=f?.id||'';$('foodName').value=f?.name||'';$('foodCategory').value=f?.category||'小吃';$('foodDefaultTime').value=dt(f?.default_time||'12:00');$('foodDuration').value=f?.duration_minutes||60;$('foodNote').value=f?.note||'';$('foodModalTitle').textContent=f?'编辑美食':'新增美食';open('foodModal')}
$('passwordForm').onsubmit=async e=>{
  e.preventDefault();
  $('passwordHint').textContent='正在验证…';
  try{
    await anon();

    if(!user?.id){
      throw new Error('Anonymous Sign-In 未建立有效用户会话');
    }

    const {data,error}=await supabase.rpc('unlock_trip_by_password',{
      p_password:$('tripPassword').value
    });

    if(error) throw error;
    if(data!==TRIP) throw new Error('数据库返回的旅行 ID 不匹配');

    sessionStorage.setItem(UNLOCK,'1');
    showApp();
    await load();
    await sub();
    $('passwordHint').textContent='密码验证成功。';
    toast('已进入西安之行');
  }catch(x){
    console.error('Trip unlock failed:',x);
    const msg=x?.message||x?.error_description||String(x);
    $('passwordHint').textContent='登录失败：'+msg;
    toast('登录失败：'+msg,true);
  }
}
$('lockBtn').onclick=()=>{sessionStorage.removeItem(UNLOCK);showGate()}
DAYS.forEach(d=>{$('scheduleDay').insertAdjacentHTML('beforeend',`<option value="${d.id}">${d.date} · ${d.weekday}</option>`)});
$('addReservationBtn').onclick=()=>openR();$('addPreparationBtn').onclick=()=>openP();$('addScheduleBtn').onclick=()=>openS();$('addFoodBtn').onclick=()=>openF();
$('reservationForm').onsubmit=async e=>{e.preventDefault();const id=$('reservationId').value,p={trip_id:TRIP,name:$('reservationName').value.trim(),status:$('reservationStatus').value,visit_date:$('reservationVisit').value.trim(),deadline:$('reservationDeadline').value.trim(),method:$('reservationMethod').value.trim(),note:$('reservationNote').value.trim()},q=id?supabase.from('reservations').update(p).eq('id',id):supabase.from('reservations').insert({...p,created_by:user.id}),{error}=await q;if(error)return toast(error.message,true);close('reservationModal');await load()}
$('scheduleForm').onsubmit=async e=>{e.preventDefault();const id=$('scheduleId').value,p={trip_id:TRIP,day:$('scheduleDay').value,start_time:$('scheduleStart').value,duration_minutes:Number($('scheduleDuration').value),title:$('scheduleTitle').value.trim(),note:$('scheduleNote').value.trim(),type:$('scheduleType').value},q=id?supabase.from('schedule_items').update(p).eq('id',id):supabase.from('schedule_items').insert({...p,priority:false,tags:p.type==='food'?['美食']:['自定义'],created_by:user.id}),{error}=await q;if(error)return toast(error.message,true);close('scheduleModal');await load()}
$('preparationForm').onsubmit=async e=>{e.preventDefault();const id=$('preparationId').value,p={trip_id:TRIP,name:$('preparationName').value.trim(),category:$('preparationCategory').value.trim()||'其他',note:$('preparationNote').value.trim(),is_done:$('preparationDone').checked},q=id?supabase.from('preparation_items').update(p).eq('id',id).eq('trip_id',TRIP):supabase.from('preparation_items').insert({...p,created_by:user.id}),{error}=await q;if(error)return toast(error.message,true);close('preparationModal');await load()}
$('foodForm').onsubmit=async e=>{e.preventDefault();const id=$('foodId').value,p={trip_id:TRIP,name:$('foodName').value.trim(),category:$('foodCategory').value.trim(),default_time:$('foodDefaultTime').value,duration_minutes:Number($('foodDuration').value),note:$('foodNote').value.trim()},q=id?supabase.from('foods').update(p).eq('id',id):supabase.from('foods').insert({...p,created_by:user.id}),{error}=await q;if(error)return toast(error.message,true);close('foodModal');await load()}
document.querySelectorAll('[data-close]').forEach(b=>b.onclick=()=>close(b.dataset.close));document.querySelectorAll('.modal-backdrop').forEach(m=>m.onclick=e=>{if(e.target===m)m.classList.remove('open')});window.addEventListener('offline',()=>sync(false,'离线 · 显示缓存'));window.addEventListener('online',()=>load().catch(()=>{}));boot();
