# Coleta automática

Scripts usados pela tarefa agendada (a cada hora):

- `plano.py` — lê as viagens nas issues "Monitorar: ..." (abertas = monitorar; fechadas = parar) e monta as buscas.
- `google.js`, `maxmilhas.js`, `decolar.js` — leem os preços nas páginas de resultado.
- `merge.py` — junta tudo ao histórico em `data/` e calcula os alertas.

Só issues criadas pelo dono do repositório são aceitas.
