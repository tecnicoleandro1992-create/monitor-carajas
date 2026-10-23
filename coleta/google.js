{ const t0=Date.now(); while(!document.body.innerText.includes('Selecionar voo') && Date.now()-t0<30000) await new Promise(r=>setTimeout(r,1000)); await new Promise(r=>setTimeout(r,1500)); }
{ const b=[...document.querySelectorAll('button')].find(x=>x.innerText.includes('Mostrar mais voos')); if(b){b.click(); await new Promise(r=>setTimeout(r,3500));} }
const toMin=s=>{const h=(s.match(/(\d+)\s*h/)||[0,0])[1], m=(s.match(/(\d+)\s*min/)||[0,0])[1]; return (+h)*60+(+m);};
const rows=[]; const seen=new Set();
for (const li of document.querySelectorAll('li')) {
  const txt=li.innerText.replace(/\n+/g,' ');
  if(!txt.includes('Selecionar voo')) continue;
  const lab=[...li.querySelectorAll('[aria-label]')].map(e=>e.getAttribute('aria-label')).find(a=>/^A partir de/.test(a));
  if(!lab) continue;
  const price=+(lab.match(/A partir de ([\d.]+) Reais/)||[0,'0'])[1].replace(/\./g,'');
  const air=(lab.match(/Voos? d[aeo]s? (.+?)(?: com \d+ parada| sem escalas|\. Sai)/)||[0,''])[1];
  const st=+(lab.match(/com (\d+) parada/)||[0,0])[1];
  const t=lab.match(/às (\d\d:\d\d) do dia .+? e chega .+? às (\d\d:\d\d) do dia [^,]+, \w+ (\d+)/);
  const dep=lab.match(/às \d\d:\d\d do dia [^,]+, \w+ (\d+)/);
  const dur=toMin((lab.match(/Duração total: ([^.]+)\./)||[0,''])[1]);
  const tail=txt.split('Selecionar voo').pop();
  const codes=tail.match(/\d\d:\d\d([A-Z]{3})\d\d:\d\d(?:\+\d)?([A-Z]{3})/)||[0,'',''];
  const via=((tail.match(/parada[s]? em ((?:[A-Z]{3}(?:, )?)+)/)||[0,''])[1]).replace(/\s/g,'');
  const plus=t&&dep? (+t[3]-(+dep[1]) + 31)%31 : 0;
  const key=[t&&t[1],codes[1],via,price].join('|'); if(seen.has(key)) continue; seen.add(key);
  rows.push({partida:t?t[1]:'',chegada:t?t[2]:'',chegada_mais_dias:plus,origem:codes[1],destino:codes[2],cia:air,escalas:st,conexoes:via,duracao_min:dur,preco_total:price,preco_pp:Math.round(price/2*100)/100});
}
JSON.stringify(rows)
