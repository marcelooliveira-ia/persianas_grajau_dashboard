// Teste do painel gerado. Uso: node tests/check.js [caminho/index.html]
// Requer playwright (já instalado no ambiente) e d3: D3_PATH=/caminho/d3.min.js (padrão /tmp/t/node_modules/d3/dist/d3.min.js).
// Instalar d3 local: mkdir -p /tmp/t && cd /tmp/t && npm i d3@7.9.0
const {chromium}=require('playwright');
const path=require('path');
const fs=require('fs');
const file=path.resolve(process.argv[2]||'index.html');
const D3=process.env.D3_PATH||'/tmp/t/node_modules/d3/dist/d3.min.js';
const dump=process.env.DUMP;
(async()=>{
 const b=await chromium.launch();
 let falhas=0;
 for(const [nome,w,h] of [['computador',1280,800],['tablet',768,900],['celular',390,700],['tela pequena',320,560]]){
  const ctx=await b.newContext({viewport:{width:w,height:h}});
  const p=await ctx.newPage();
  const erros=[];
  p.on('pageerror',e=>erros.push(e.message));
  await p.route('**/d3.min.js',r=>r.fulfill({path:D3,contentType:'application/javascript'}));
  await p.route(/fonts\.(googleapis|gstatic)\.com/,r=>r.abort());
  await p.goto('file://'+file);
  await p.waitForTimeout(800);
  const H=await p.evaluate(()=>document.documentElement.scrollHeight);
  for(let y=0;y<H;y+=300){await p.evaluate(v=>window.scrollTo(0,v),y);await p.waitForTimeout(70);}
  await p.waitForTimeout(1600);
  await p.evaluate(()=>window.scrollTo(0,0));
  const geral=await p.evaluate(()=>({
   sw:document.documentElement.scrollWidth,cw:document.documentElement.clientWidth,
   cards:document.querySelectorAll('.pc').length,acoes:document.querySelectorAll('.recs .card').length,
   semRevelar:document.querySelectorAll('.rv:not(.in)').length,
   imgs:[...document.images].filter(i=>!(i.complete&&i.naturalWidth>0)).map(i=>i.getAttribute('src')),
   texto:document.body.innerText}));
  if(dump&&nome==='computador'){fs.writeFileSync(dump,geral.texto);}
  const ruins=[];
  const n=await p.locator('.pginfo').count();
  for(let i=0;i<n;i++){
   const btn=p.locator('.pginfo').nth(i);
   await btn.scrollIntoViewIfNeeded();await p.waitForTimeout(50);
   await btn.hover();await p.waitForTimeout(70);
   const r=await p.evaluate(()=>{const e=document.querySelector('.pop');const q=e.getBoundingClientRect();return {on:e.classList.contains('on'),l:q.left,r:q.right,t:q.top,b:q.bottom,vw:document.documentElement.clientWidth,vh:window.innerHeight,n:e.textContent.length};});
   if(!(r.on&&r.l>=0&&r.r<=r.vw+0.5&&r.t>=0&&r.b<=r.vh+0.5&&r.n>5)){ruins.push(i);}
   await p.mouse.move(2,2);await p.waitForTimeout(30);
  }
  const problemas=[];
  if(geral.sw>geral.cw)problemas.push('rolagem horizontal');
  if(erros.length)problemas.push('erros de script: '+erros.join('; '));
  if(geral.imgs.length)problemas.push('imagens sem carregar: '+geral.imgs.join(', '));
  if(geral.semRevelar)problemas.push('blocos que não apareceram: '+geral.semRevelar);
  if(!geral.cards)problemas.push('sem cartões de plataforma');
  if(ruins.length)problemas.push('balões fora da tela: '+ruins.join(','));
  console.log(nome.padEnd(13),'ícones:',n,problemas.length?'PROBLEMAS -> '+problemas.join(' | '):'ok');
  falhas+=problemas.length;
  await ctx.close();
 }
 await b.close();
 process.exit(falhas?1:0);
})();
