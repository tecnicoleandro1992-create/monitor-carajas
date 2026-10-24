"""Monta o plano de buscas de uma coleta.

Uso: python3 coleta/plano.py COLETA_ID [pasta_data]
- Lê as viagens das issues do repositório (abertas = monitorar; fechadas = encerradas),
  aceitando só issues criadas pelo dono do repositório e com título começando por "Monitorar".
- Gera plano.json (lista de buscas) e viagens.json no diretório atual.
"""
import base64, datetime as dt, json, os, re, sys, urllib.request

OWNER, REPO = 'tecnicoleandro1992-create', 'monitor-carajas'
MAX_VIAGENS, MAX_GOOGLE = 4, 20
cid = sys.argv[1]
data_dir = sys.argv[2] if len(sys.argv) > 2 else 'repo/data'
hoje = cid[:10]

# ---------- URL do Google Voos (parâmetro tfs) ----------
def _v(n):
    out = b''
    while True:
        b = n & 0x7f; n >>= 7
        if n: out += bytes([b | 0x80])
        else: return out + bytes([b])
def _f(num, wt, p):
    k = _v((num << 3) | wt)
    return k + _v(p) if wt == 0 else k + _v(len(p)) + p
def _place(kind, code): return _f(1, 0, kind) + _f(2, 2, code.encode())
RIO, CKS = (2, '/m/06gmr'), (1, 'CKS')
def url_google(sentido, data, adultos):
    a, b = (RIO, CKS) if sentido == 'ida' else (CKS, RIO)
    leg = _f(2, 2, data.encode()) + _f(13, 2, _place(*a)) + _f(14, 2, _place(*b))
    raw = _f(1, 0, 28) + _f(2, 0, 2) + _f(3, 2, leg) + b''.join(_f(8, 0, 1) for _ in range(adultos)) \
        + _f(9, 0, 1) + _f(14, 0, 1) + _f(16, 2, bytes.fromhex('08ffffffffffffffffff01')) + _f(19, 0, 2)
    return 'https://www.google.com/travel/flights/search?tfs=' + base64.urlsafe_b64encode(raw).decode().rstrip('=') + '&hl=pt-BR&gl=BR&curr=BRL'
def url_maxmilhas(v): return f"https://www.maxmilhas.com.br/busca-passagens-aereas/RT/RIO/CKS/{v['ida']}/{v['volta']}/{v['adultos']}/0/0/EC"
def url_decolar(v): return f"https://www.decolar.com/shop/flights/results/roundtrip/rio/cks/{v['ida']}/{v['volta']}/{v['adultos']}/0/0"

# ---------- viagens ----------
def vid(ida, volta, ad, flex): return f'{ida}_{volta}_{ad}a_f{flex}'
def parse(body):
    g = lambda k: (re.search(k + r'\s*[:=]\s*([0-9-]+)', body or '', re.I) or [None, None])[1]
    try:
        ida, volta = g('ida'), g('volta')
        ad, fx = int(g('adultos') or 2), int(g('flexibilidade') or 0)
        dt.date.fromisoformat(ida); dt.date.fromisoformat(volta)
        if volta <= ida or not (1 <= ad <= 9) or not (0 <= fx <= 3): return None
        return {'ida': ida, 'volta': volta, 'adultos': ad, 'flex': fx}
    except Exception:
        return None

anteriores = []
p = os.path.join(data_dir, 'viagens.json')
if os.path.exists(p):
    try: anteriores = json.load(open(p))
    except Exception: anteriores = []

viagens, erro_api = {}, ''
try:
    req = urllib.request.Request(f'https://api.github.com/repos/{OWNER}/{REPO}/issues?state=all&per_page=100',
                                 headers={'Accept': 'application/vnd.github+json', 'User-Agent': 'monitor-carajas',
                                          **({'Authorization': 'Bearer ' + os.environ['GH_TOKEN']} if os.environ.get('GH_TOKEN') else {})})
    issues = json.load(urllib.request.urlopen(req, timeout=20))
    for it in sorted(issues, key=lambda x: x['number']):
        if 'pull_request' in it or (it.get('user') or {}).get('login') != OWNER: continue
        if not it.get('title', '').strip().lower().startswith('monitorar'): continue
        d = parse(it.get('body'))
        if not d: continue
        i = vid(d['ida'], d['volta'], d['adultos'], d['flex'])
        ativa = it['state'] == 'open' and d['ida'] >= hoje
        if i in viagens and viagens[i]['status'] == 'ativa' and not ativa: continue  # uma issue aberta vale mais que uma fechada repetida
        viagens[i] = {**d, 'id': i, 'issue': it['number'], 'issue_url': it['html_url'],
                      'status': 'ativa' if ativa else 'encerrada', 'criada_em': it['created_at']}
except Exception as e:
    erro_api = f'Não consegui ler as viagens no GitHub ({e.__class__.__name__}); usei a lista anterior.'
    for a in anteriores:
        viagens[a['id']] = {**a, 'status': a['status'] if a['ida'] >= hoje else 'encerrada'}
for a in anteriores:  # viagens antigas cuja issue sumiu continuam no histórico
    if a['id'] not in viagens: viagens[a['id']] = {**a, 'status': 'encerrada'}

ativas = [v for v in viagens.values() if v['status'] == 'ativa']
ativas.sort(key=lambda v: v.get('issue', 0))
for v in ativas[MAX_VIAGENS:]: v['status'] = 'fila'
ativas = ativas[:MAX_VIAGENS]

# ---------- plano ----------
plano, google = [], {}
def add_google(sent, data, ad):
    k = (sent, data, ad)
    if k in google: return True
    if len(google) >= MAX_GOOGLE: return False
    if data < hoje: return True
    google[k] = {'tipo': 'google', 'sentido': sent, 'data': data, 'adultos': ad,
                 'arquivo': f'g_{sent}_{data}_{ad}.json', 'url': url_google(sent, data, ad)}
    return True
for v in ativas:  # datas exatas primeiro, depois as vizinhas
    add_google('ida', v['ida'], v['adultos']); add_google('volta', v['volta'], v['adultos'])
for v in ativas:
    v['flex_usada'] = v['flex']
    for d in range(1, v['flex'] + 1):
        ok = True
        for base, sent in ((v['ida'], 'ida'), (v['volta'], 'volta')):
            for s in (-d, d):
                day = (dt.date.fromisoformat(base) + dt.timedelta(days=s)).isoformat()
                ok = add_google(sent, day, v['adultos']) and ok
        if not ok:
            v['flex_usada'] = d - 1; v['aviso'] = f'Flexibilidade reduzida para ±{d - 1} dia(s) para não sobrecarregar a coleta.'; break
plano += list(google.values())
for v in ativas:
    plano.append({'tipo': 'maxmilhas', 'viagem': v['id'], 'arquivo': f"mm_{v['id']}.json", 'url': url_maxmilhas(v)})
    plano.append({'tipo': 'decolar', 'viagem': v['id'], 'arquivo': f"dec_{v['id']}.json", 'url': url_decolar(v)})

lista = sorted(viagens.values(), key=lambda v: ({'ativa': 0, 'fila': 1, 'encerrada': 2}[v['status']], v.get('issue', 0)))
json.dump(plano, open('plano.json', 'w'), ensure_ascii=False, indent=1)
json.dump(lista, open('viagens.json', 'w'), ensure_ascii=False, indent=1)
print(json.dumps({'viagens_ativas': [v['id'] for v in ativas], 'buscas': len(plano), 'aviso_api': erro_api}, ensure_ascii=False))
