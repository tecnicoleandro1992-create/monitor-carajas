{ const t0=Date.now(); while(!document.body.innerText.includes('Preço final') && Date.now()-t0<30000) await new Promise(r=>setTimeout(r,1000)); await new Promise(r=>setTimeout(r,1500)); }
const t=document.body.innerText;
const blocks=t.split(/Despegar Catalog/).slice(1);
const toMin=s=>{const h=(s.match(/(\d+)h/)||[0,0])[1], m=(s.match(/(\d+)m/)||[0,0])[1]; return (+h)*60+(+m);};
const leg=(s)=>{ if(!s) return null; const L=s.split('\n').map(x=>x.trim()).filter(Boolean);
  const i=L.findIndex(x=>x==='Bagagem'); const codes=L.filter(x=>/^[A-Z]{3}$/.test(x));
  const times=L.filter(x=>/^\d\d:\d\d$/.test(x)); const plus=L.includes('+1')?1:0;
  const st=(L.find(x=>/parada|Direto/i.test(x))||''); const dur=L.find(x=>/^\d+h( \d+m)?$|^\d+m$/.test(x))||'';
  return {cia:(L[i+1]||'').trim(),origem:codes[0]||'',destino:codes[1]||'',partida:times[0]||'',chegada:times[1]||'',chegada_mais_dias:plus,escalas:/Direto/i.test(st)?0:+(st.match(/\d+/)||[0])[0],duracao_min:toMin(dur)}; };
const out=[];
for(const b of blocks){
  const pf=b.match(/Preço final\s*R\$\s*([\d.]+)/); if(!pf) continue;
  const [, ida, volta]=b.split(/\bIDA\b|\bVOLTA\b/);
  out.push({ida:leg(ida),volta:leg(volta),preco_total:+pf[1].replace(/\./g,''),tarifa:(b.match(/Adicione [^\n]+/)||[''])[0]});
}
JSON.stringify(out.slice(0,15))
