"""Empacota os resultados de uma coleta para enviar ao GitHub como comentário.

Uso: python3 coleta/payload.py COLETA_ID  (no diretório da coleta)
Lê plano.json, viagens.json e os arquivos de resultado; grava comentario.txt.
O workflow .github/workflows/site.yml desempacota e roda merge.py no repositório.
"""
import base64, gzip, json, os, sys

cid = sys.argv[1]
plano = json.load(open('plano.json'))
pacote = {'coleta_id': cid, 'plano': plano, 'viagens': json.load(open('viagens.json')), 'resultados': {}}
for it in plano:
    if os.path.exists(it['arquivo']) and os.path.getsize(it['arquivo']) > 0:
        pacote['resultados'][it['arquivo']] = json.load(open(it['arquivo']))
dados = base64.b64encode(gzip.compress(json.dumps(pacote, ensure_ascii=False).encode())).decode()
texto = f'Coleta {cid} (enviada automaticamente; o site se atualiza sozinho)\n\n<!--coleta\n{dados}\n-->\n'
open('comentario.txt', 'w').write(texto)
print(len(texto))
