(() => {
 const root=document.documentElement;let saved;
 try{saved=localStorage.getItem('showball-theme')}catch{}
 root.dataset.theme=['light','dark'].includes(saved)?saved:matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light';
 const sync=()=>document.querySelectorAll('[data-theme-toggle]').forEach(b=>{b.textContent=root.dataset.theme==='dark'?'浅色':'深色';b.setAttribute('aria-label',`切换到${root.dataset.theme==='dark'?'浅色':'深色'}模式`)});
 document.addEventListener('click',e=>{
  if(e.target.closest('[data-theme-toggle]')){root.dataset.theme=root.dataset.theme==='dark'?'light':'dark';try{localStorage.setItem('showball-theme',root.dataset.theme)}catch{}sync()}
  const menu=document.querySelector('[data-menu-toggle]');
  if(e.target.closest('[data-menu-toggle]')){const open=document.body.classList.toggle('nav-open');menu?.setAttribute('aria-expanded',String(open))}
  if(e.target.closest('.nav-card')){document.body.classList.remove('nav-open');menu?.setAttribute('aria-expanded','false')}
 });
 document.addEventListener('keydown',e=>{if(e.key==='Escape'&&document.body.classList.contains('nav-open')){document.body.classList.remove('nav-open');const m=document.querySelector('[data-menu-toggle]');m?.setAttribute('aria-expanded','false');m?.focus()}});
 document.querySelectorAll('.nav-card[data-page]').forEach(a=>{if(a.dataset.page===document.body.dataset.page)a.setAttribute('aria-current','page')});
 function tick(){const c=document.getElementById('clock');if(!c)return;const d=new Date(),p=n=>String(n).padStart(2,'0');c.textContent=`${d.getFullYear()}-${p(d.getMonth()+1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`}
 tick();setInterval(tick,1000);sync();
})();
