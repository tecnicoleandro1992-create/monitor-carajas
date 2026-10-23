await new Promise(r=>setTimeout(r,6000));
const toMin=s=>{const h=(s.match(/(\d+)h/)||[0,0])[1], m=(s.match(/h(\d+)m|^(\d+)m/)||[0,0,0]); return (+h)*60+(+(m[1]||m[2]||0));};
const leg=(s)=>{ if(!s) return null; const L=s.split('\n').map(x=>x.trim()).filter(Boolean);
  const codes=L.filter(x=>/^[A-Z]{3}$/.test(x)); const times=L.filter(x=>/^\d\d:\d\d$/.test(x));
  const st=L.find(x=>/parada|direto/i.test(x))||''; const dur=L.find(x=>/^\d+h\d*m?$|^\d+m$/.test(x))||'';
  return {cia:L[1]||'',origem:codes[0]||'',destino:codes[1]||'',partida:times[0]||'',chegada:times[1]||'',chegada_mais_dias:L.includes('+1')?1:0,escalas:/direto/i.test(st)?0:+(st.match(/\d+/)||[0])[0],duracao_min:toMin(dur)}; };
const seen=new Map();
const grab=()=>{ const t=document.body.innerText;
  for(const b of t.split(/\n\s*Ida - /).slice(1)){
    const vt=b.match(/Valor total\s*R\$\s*([\d.]+,\d\d)/); if(!vt) continue;
    const [idaTxt, rest]=b.split(/\n\s*Volta - /);
    const voltaTxt=(rest||'').split(/Até \d+kg|Econômica|Precisa de bagagem/)[0];
    const r={ida:leg(idaTxt),volta:leg(voltaTxt),preco_total:Math.round(+vt[1].replace(/\./g,'').replace(',','.')),pix:/No PIX/.test(b),mala_mao:(b.match(/Até (\d+)kg/)||[0,''])[1]};
    const k=JSON.stringify([r.ida,r.volta,r.preco_total]); if(!seen.has(k)) seen.set(k,r);
  } };
window.scrollTo(0,0); await new Promise(r=>setTimeout(r,800)); grab();
for(let y=0;y<document.body.scrollHeight && seen.size<30;y+=Math.round(window.innerHeight*0.6)){ window.scrollTo(0,y); await new Promise(r=>setTimeout(r,700)); grab(); }
window.scrollTo(0,0);
JSON.stringify([...seen.values()].sort((a,b)=>a.preco_total-b.preco_total).slice(0,15))
