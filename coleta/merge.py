"""Junta os resultados de uma coleta ao histórico.

Uso: python3 coleta/merge.py COLETA_ID PASTA_DATA
Lê plano.json, viagens.json e os arquivos de resultado do diretório atual,
mais o histórico em PASTA_DATA/{ofertas,coletas,combos}.json.
Grava o histórico atualizado em PASTA_DATA (ofertas, coletas, combos, viagens).
"""
import datetime as dt, json, os, sys

cid, data_dir = sys.argv[1], sys.argv[2]
def ld(p, d):
    try:
        return json.load(open(p)) if os.path.exists(p) and os.path.getsize(p) > 0 else d
    except Exception:
        return d
H = lambda n: os.path.join(data_dir, n)
ofertas, coletas, combos = ld(H('ofertas.json'), []), ld(H('coletas.json'), []), ld(H('combos.json'), [])
plano, viagens = ld('plano.json', []), ld('viagens.json', [])
fmt = lambda v: 'R$ ' + f'{v:,.0f}'.replace(',', '.')

# migração de linhas antigas (antes de existir mais de uma viagem)
for o in ofertas: o.setdefault('adultos', 2)
for c in combos:
    c.setdefault('data_ida', '2026-11-25'); c.setdefault('data_volta', '2026-11-30'); c.setdefault('adultos', 2)

ativas = [v for v in viagens if v.get('status') == 'ativa']
def rng(base, f):
    b = dt.date.fromisoformat(base); return {(b + dt.timedelta(days=d)).isoformat() for d in range(-f, f + 1)}
def total_viagem(v, ofs, cbs, coleta):
    """Melhor ida+volta da viagem v numa coleta: Google (melhor par de datas) e agências."""
    f = v.get('flex_usada', v.get('flex', 0)); ri, rv = rng(v['ida'], f), rng(v['volta'], f)
    mi, mv = {}, {}
    for o in ofs:
        if o['coleta_id'] != coleta or int(o.get('adultos', 2)) != int(v['adultos']): continue
        p = float(o['preco_total'])
        if o['sentido'] == 'ida' and o['data_voo'] in ri: mi[o['data_voo']] = min(p, mi.get(o['data_voo'], 1e12))
        if o['sentido'] == 'volta' and o['data_voo'] in rv: mv[o['data_voo']] = min(p, mv.get(o['data_voo'], 1e12))
    cands = []
    g = [(mi[a] + mv[b], a, b) for a in mi for b in mv if b > a]
    if g: cands.append((min(g)[0], 'Google Voos (GOL)'))
    for c in cbs:
        if c['coleta_id'] == coleta and c['data_ida'] == v['ida'] and c['data_volta'] == v['volta'] and int(c['adultos']) == int(v['adultos']):
            cands.append((float(c['preco_total']), c['vendedor']))
    return (min(g)[0] if g else None), (min(cands) if cands else None)

# ---------- resultados desta coleta ----------
novas, novos_combos, st = [], [], {'google': [0, 0], 'maxmilhas': [0, 0], 'decolar': [0, 0]}
for it in plano:
    res = ld(it['arquivo'], None)
    ok = isinstance(res, list) and len(res) > 0
    st[it['tipo']][0 if ok else 1] += 1
    if not ok: continue
    if it['tipo'] == 'google':
        for r in res:
            if not r.get('preco_total'): continue
            vid = '|'.join([it['sentido'], it['data'], r['partida'], r['origem'], r['destino'], r['conexoes'], str(it['adultos'])])
            novas.append({'coleta_id': cid, 'coletado_em': cid, 'sentido': it['sentido'], 'data_voo': it['data'], 'adultos': it['adultos'],
                          'voo_id': vid, **r, 'fonte': 'Google Voos'})
    else:
        v = next((x for x in viagens if x['id'] == it['viagem']), None)
        if not v: continue
        vend = 'MaxMilhas' if it['tipo'] == 'maxmilhas' else 'Decolar'
        for r in res:
            i, w = r.get('ida') or {}, r.get('volta') or {}
            if not r.get('preco_total') or not i.get('partida') or not w.get('partida'): continue
            novos_combos.append({'coleta_id': cid, 'coletado_em': cid, 'vendedor': vend, 'data_ida': v['ida'], 'data_volta': v['volta'], 'adultos': v['adultos'],
                'combo_id': '|'.join([vend, v['ida'], v['volta'], str(v['adultos']), i['origem'], i['partida'], i.get('cia', ''), w['destino'], w['partida'], w.get('cia', '')]),
                'ida_cia': i.get('cia', ''), 'ida_origem': i['origem'], 'ida_partida': i['partida'], 'ida_chegada': i.get('chegada', ''),
                'ida_mais_dias': i.get('chegada_mais_dias', 0), 'ida_escalas': i.get('escalas', 0), 'ida_duracao_min': i.get('duracao_min', 0),
                'volta_cia': w.get('cia', ''), 'volta_destino': w['destino'], 'volta_partida': w['partida'], 'volta_chegada': w.get('chegada', ''),
                'volta_mais_dias': w.get('chegada_mais_dias', 0), 'volta_escalas': w.get('escalas', 0), 'volta_duracao_min': w.get('duracao_min', 0),
                'preco_total': int(r['preco_total']), 'obs': 'preço no PIX' if r.get('pix') else (r.get('tarifa') or '')})

# ---------- alertas por viagem ----------
alertas = []
ant_ids = sorted({o['coleta_id'] for o in ofertas} | {c['coleta_id'] for c in combos})
for v in ativas:
    nome = f"{v['ida'][8:10]}/{v['ida'][5:7]} → {v['volta'][8:10]}/{v['volta'][5:7]} ({v['adultos']} adulto{'s' if v['adultos'] > 1 else ''})"
    g_now, best_now = total_viagem(v, novas, novos_combos, cid)
    hist_g, hist_b = [], []
    for k in ant_ids:
        g, b = total_viagem(v, ofertas, combos, k)
        if g is not None: hist_g.append(g)
        if b is not None: hist_b.append(b[0])
    if best_now and hist_b and best_now[0] < min(hist_b):
        alertas.append(f'NOVO MENOR PREÇO {nome}: {fmt(best_now[0])} em {best_now[1]} (antes {fmt(min(hist_b))})')
    elif g_now is not None and hist_g and g_now < min(hist_g):
        alertas.append(f'Novo menor preço no Google Voos {nome}: {fmt(g_now)} (antes {fmt(min(hist_g))})')
    if g_now is not None and len(hist_g) + 1 >= 24:
        media = (sum(hist_g) + g_now) / (len(hist_g) + 1)
        if g_now <= media * 0.85:
            alertas.append(f'BOA OPORTUNIDADE {nome}: {fmt(g_now)}, {round((1 - g_now / media) * 100)}% abaixo da média {fmt(media)}')

def s(k):
    ok, bad = st[k]
    return 'ok' if ok and not bad else 'parcial' if ok else ('falha' if bad else '—')
erros = [v.get('aviso') for v in ativas if v.get('aviso')]
coletas.append({'coleta_id': cid, 'coletado_em': cid, 'status': s('google'),
                'ofertas_ida': sum(1 for n in novas if n['sentido'] == 'ida'), 'ofertas_volta': sum(1 for n in novas if n['sentido'] == 'volta'),
                'maxmilhas': s('maxmilhas'), 'decolar': s('decolar'), 'combos_agencias': len(novos_combos),
                'viagens_ativas': len(ativas), 'alerta': ' | '.join(alertas), 'erro': ' '.join(erros)})
for c in coletas:
    for k, d in (('maxmilhas', ''), ('decolar', ''), ('combos_agencias', 0), ('viagens_ativas', 1)): c.setdefault(k, d)
ofertas += novas; combos += novos_combos
for n, obj in (('ofertas.json', ofertas), ('coletas.json', coletas), ('combos.json', combos), ('viagens.json', viagens)):
    json.dump(obj, open(H(n), 'w'), ensure_ascii=False)
melhores = {}
for v in ativas:
    _, b = total_viagem(v, novas, novos_combos, cid)
    if b: melhores[v['id']] = f'{fmt(b[0])} em {b[1]}'
print(json.dumps({'google': st['google'], 'maxmilhas': st['maxmilhas'], 'decolar': st['decolar'],
                  'novas': len(novas), 'combos': len(novos_combos), 'melhor_por_viagem': melhores, 'alertas': alertas}, ensure_ascii=False))
