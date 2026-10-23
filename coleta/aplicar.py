"""Usado pelo workflow: desempacota o comentário de uma coleta e roda o merge.

Uso: python3 coleta/aplicar.py ARQUIVO_COM_O_COMENTARIO
"""
import base64, gzip, json, os, re, subprocess, sys, tempfile

texto = open(sys.argv[1]).read()
m = re.search(r'<!--coleta\s+([A-Za-z0-9+/=\s]+?)\s*-->', texto)
if not m:
    sys.exit('comentário sem dados de coleta')
pacote = json.loads(gzip.decompress(base64.b64decode(''.join(m.group(1).split()))))
cid = pacote['coleta_id']
if not re.fullmatch(r'\d{4}-\d\d-\d\dT\d\d:\d\d-03:00', cid):
    sys.exit('COLETA_ID inválido')
data_dir = os.path.abspath('data')
existentes = {c['coleta_id'] for c in json.load(open(os.path.join(data_dir, 'coletas.json')))}
if cid in existentes:
    print('coleta já aplicada'); sys.exit(0)
with tempfile.TemporaryDirectory() as tmp:
    json.dump(pacote['plano'], open(os.path.join(tmp, 'plano.json'), 'w'))
    json.dump(pacote['viagens'], open(os.path.join(tmp, 'viagens.json'), 'w'))
    for nome, conteudo in pacote['resultados'].items():
        if re.fullmatch(r'[\w.-]+\.json', nome):
            json.dump(conteudo, open(os.path.join(tmp, nome), 'w'))
    subprocess.run([sys.executable, os.path.abspath('coleta/merge.py'), cid, data_dir], cwd=tmp, check=True)
