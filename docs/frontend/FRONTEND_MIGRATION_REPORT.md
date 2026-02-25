# FRONTEND_MIGRATION_REPORT

## 1) O que foi movido e para onde

- Movido frontend legado:
  - `igreja_dashboard_python/templates` → `frontend/legacy/igreja_dashboard_python/templates`
  - `igreja_dashboard_python/static` → `frontend/legacy/igreja_dashboard_python/static`
- Mantidos symlinks de compatibilidade no caminho original para evitar quebra do legado Python.

## 2) O que foi criado na nova stack PHP

- Estrutura web nova:
  - `routes/web.php` (mapa de rotas de telas)
  - `resources/views/layouts/app.php` (layout global: sidebar, menu mobile, busca global, FAB Novo)
  - `resources/views/pages/generic.php` (scaffold de tela com estado loading/vazio/erro, filtros/tabela/timeline)
  - `resources/views/errors/forbidden.php` (permissão negada)
  - `src/Http/WebFrontend.php` (matcher + renderer de views)
  - `public/index.php` atualizado para servir rotas web antes das APIs JSON.

## 3) Rotas implementadas e status

| Rota | Status |
|---|---|
| `/login` | stub |
| `/recuperar-senha` | stub |
| `/dashboard` | stub |
| `/familias` | stub |
| `/familias/nova` | stub |
| `/familias/{id}` | stub |
| `/pessoas` | stub |
| `/pessoas/novo-atendimento` | stub |
| `/pessoas/{id}` | stub |
| `/criancas` | stub |
| `/criancas/nova` | stub |
| `/criancas/{id}/editar` | stub |
| `/entregas/eventos` | stub |
| `/entregas/eventos/novo` | stub |
| `/entregas/eventos/{id}/convidados` | stub |
| `/entregas/eventos/{id}/criancas` | stub |
| `/equipamentos` | stub |
| `/equipamentos/novo` | stub |
| `/equipamentos/{id}` | stub |
| `/equipamentos/emprestimos` | stub |
| `/relatorios/mensais` | stub |
| `/admin/usuarios` | stub + gate inicial |
| `/admin/config` | stub + gate inicial |

Compatibilidade adicional também scaffoldada para aliases solicitados pelo cliente:
- `/entregas/eventos/{id}`
- `/relatorios`
- `/admin/configuracoes`

## 4) Gaps vs SCREEN_RULES.md

- Dados reais por tela ainda dependem de contrato final de APIs (`docs/frontend/API_CONTRACT_TBD.md`).
- Componentes de tela estão scaffoldados (não finalizados com dados produtivos).
- Gate de admin é inicial via header `X-User-Role=admin`; precisa convergir para middleware/autenticação definitiva.

## 5) Próximos passos (alinhados ao plano)

- Sprint 03: integração de autenticação/perfis no frontend web.
- Sprint 04–06: ligar telas de famílias/pessoas/crianças/entregas aos endpoints já existentes.
- Sprint 08–09: concluir equipamentos, relatórios e admin config com contratos estabilizados.
