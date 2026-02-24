# UX — Busca global

## Endpoint
- `GET /busca?q=...`

## Escopo
- Famílias (responsável/CPF/bairro)
- Crianças (nome)
- Equipamentos (código/descrição)
- Eventos de entrega (título)

## UI
- Campo de busca global adicionado na navbar para usuários autenticados.
- Resultado SSR em `templates/search_results.html` com seções por domínio.
