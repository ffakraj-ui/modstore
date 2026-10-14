(function(){
var q=function(s){return document.querySelector(s)};
var esc=function(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]})};
var mb=q('#mb'),sb=q('#sb'),ov=q('#ov');
function tog(o){sb.classList.toggle('open',o);ov.classList.toggle('on',o);mb.setAttribute('aria-expanded',o)}
mb.onclick=function(){tog(!sb.classList.contains('open'))};ov.onclick=function(){tog(false)};
document.addEventListener('keydown',function(e){if(e.key==='Escape')tog(false)});
var L=q('#list');
if(L){
 var P=new URLSearchParams(location.search),S={q:P.get('q')||'',cat:P.get('cat')||'',sort:P.get('sort')||'dn',safe:P.get('safe')==='1',n:60},A=[];
 var f=q('#sb form');f.q.value=S.q;f.cat.value=S.cat;f.sort.value=S.sort;f.safe.checked=S.safe;
 var sq=q('#sq');if(sq){sq.value=S.q;sq.focus();sq.oninput=function(){S.q=sq.value;S.n=60;render();history.replaceState(null,'','?q='+encodeURIComponent(S.q))}}
 var so={dn:function(a,b){return b.dn-a.dn},new:function(a,b){return b.id-a.id},r:function(a,b){return b.r-a.r||b.dn-a.dn},n:function(a,b){return a.n.localeCompare(b.n)},sz:function(a,b){return a.mb-b.mb}};
 var card=function(x){return '<a class="card" href="app/'+esc(x.s)+'.html"><img class="ic" src="'+esc(x.i)+'" width="56" height="56" alt="'+esc(x.n)+' icon" loading="lazy" referrerpolicy="no-referrer" onerror="this.style.visibility=\'hidden\'"><span class="ct"><b>'+esc(x.n)+'</b><small>'+esc(x.a)+'</small><small>'+esc(x.c)+' · v'+esc(x.v)+' · '+x.mb+' MB</small></span></a>'};
 var render=function(){var s=S.q.toLowerCase(),l=A.filter(function(x){return(!S.cat||x.cs===S.cat)&&(!S.safe||x.sec==='safe')&&(!s||(x.n+' '+x.a+' '+x.p).toLowerCase().indexOf(s)>-1)}).sort(so[S.sort]||so.dn);
  q('#meta').textContent=l.length+' apps';q('#grid').innerHTML=l.slice(0,S.n).map(card).join('')||'<p class="empty">Kuch nahi mila. Doosra naam ya filter try karo.</p>';q('#more').hidden=S.n>=l.length};
 q('#more').onclick=function(){S.n+=60;render()};
 fetch('index.json').then(function(r){return r.json()}).then(function(d){A=d;render()});
}
var D=q('#dl'),G=q('#go');
if(D&&G){G.onclick=function(){
 var u=atob(D.dataset.u),s=D.dataset.s,end=Date.now()+10000;
 D.innerHTML='<div class="cd" role="status" aria-live="polite">Please wait <b id="n">10</b> seconds…<i><u id="bar"></u></i></div>';
 var h=setInterval(function(){var r=Math.max(0,Math.ceil((end-Date.now())/1000));q('#n').textContent=r;q('#bar').style.width=(100-r*10)+'%';
  if(r<=0){clearInterval(h);var b=document.createElement('button');b.className='btn xl go';b.textContent='⬇ Download App';
   b.onclick=function(){if((s==='malware'||s==='suspicious')&&!confirm('Ye APK "'+s+'" flag hai. Phir bhi download karna hai?'))return;location.href=u};
   D.innerHTML='';D.appendChild(b);b.focus()}},200)}}
})();
                                               
