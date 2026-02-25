# LEGACY Frontend Isolado

Este diretório concentra o frontend legado originalmente servido pelo projeto Python/FastAPI (`igreja_dashboard_python/templates` + `igreja_dashboard_python/static`).

## O que foi movido
- `igreja_dashboard_python/templates` → `frontend/legacy/igreja_dashboard_python/templates`
- `igreja_dashboard_python/static` → `frontend/legacy/igreja_dashboard_python/static`

Para evitar quebra de referências ativas no backend legado, foram deixados *symlinks* compatíveis nos caminhos originais.

## Como executar o legado
No contexto do app Python legado:

```bash
cd igreja_dashboard_python
uvicorn app.main:app --reload
```

O FastAPI continuará resolvendo `templates/` e `static/` pelos links simbólicos.

## Motivo do isolamento
- separar explicitamente o frontend legado do novo frontend em PHP;
- facilitar migração incremental com rastreabilidade;
- reduzir risco de regressão por mistura de stacks.
