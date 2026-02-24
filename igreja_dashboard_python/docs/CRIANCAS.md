# Módulo de Crianças

## Objetivo
Cadastro dedicado de crianças com vínculo à família, filtros por idade/sexo/família e integração com eventos de entrega.

## RBAC
- **Leitura** (`view_families`): pode listar e visualizar detalhes de crianças e listas por evento.
- **Operador/Admin** (`manage_families`): pode criar, editar e excluir crianças.

## Rotas SSR — Crianças
- `GET /criancas` — listagem com filtros.
- `GET /criancas/nova` — formulário de criação.
- `POST /criancas` — criação.
- `GET /criancas/{id}` — detalhe.
- `GET /criancas/{id}/edit` — formulário de edição.
- `POST /criancas/{id}` — atualização.
- `POST /criancas/{id}/delete` — exclusão.

## Regras
- `family_id`, `name` e `birth_date` são obrigatórios.
- Família deve existir e estar ativa para criar/editar criança.
- `sex` aceita valores `M`, `F`, `O`, `NI`.

## Filtros de listagem
- `family_id`
- `idade_min`
- `idade_max`
- `sexo`
- `nome`

## Integração com Eventos
- `delivery_events.has_children_list` indica se o evento usa lista de crianças.
- Endpoint de lista por evento:
  - `GET /entregas/eventos/{id}/criancas`
- Critério de família confirmada:
  - convite no evento com status `WITHDRAWN`.

## Exports
- `GET /entregas/eventos/{id}/criancas/export.xlsx`
- `GET /entregas/eventos/{id}/criancas/export.pdf`

PDF segue formato A4 com cabeçalho e tabela legível para impressão.
