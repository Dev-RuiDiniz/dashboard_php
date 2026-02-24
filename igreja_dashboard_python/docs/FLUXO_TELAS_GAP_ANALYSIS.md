# FLUXO_TELAS_GAP_ANALYSIS

Legenda: ✅ completo | 🟡 parcial | ❌ ausente

| Fase/Fluxo | Status | Evidência | Gap/ação |
|---|---|---|---|
| Auth login/reset/lockout | ✅ | `login.html`, `auth_forgot_password.html`, `auth_reset_password.html`, lockout/rate-limit no backend | Adicionado `POST /auth/login` para contrato API |
| Dashboard operacional | ✅ | `/dashboard` com queries agregadas e blocos | Mantido stack SSR |
| Famílias lista + wizard + detalhe + PDF | ✅ | `/familias`, `/familias/nova/step/{step}`, `/familias/{id}`, `/familias/{id}/export.pdf` | Sem mudança funcional |
| Pessoas/ficha social | 🟡 | Fluxo atual em `/rua` (lista/detalhe/atendimento/encaminhamento) + PDF individual | Incluído alias `/pessoas`; nomenclatura da URL diverge do documento funcional |
| Crianças CRUD + filtros | ✅ | `/criancas` + create/edit/delete | Sem gap crítico |
| Entregas eventos/convidar/retirada/exports | 🟡→✅ | Rotas de criação, convite, retirada e export já existentes | Implementados `GET /entregas/eventos`, `POST /entregas/eventos/{id}/close` e tela `/entregas` |
| Equipamentos CRUD + empréstimo/devolução | ✅ | `/equipamentos/*` + `/emprestimo` + `/devolver` | Sem gap crítico |
| Relatórios mensal + export | ✅ | `/relatorios` + exports CSV/XLSX/PDF | Sem gap crítico |
| Admin usuários/config | ✅ | `/admin/users`, `/admin/config` | Adicionado alias `/admin/usuarios` |
| UX extra (busca global/chips/timeline) | 🟡→✅ | Busca global já existente | Implementado endpoint agregador `/timeline` |
| Navegação obrigatória sem 404 | ✅ | rotas-chave presentes (`/dashboard`, `/familias`, `/pessoas`, `/criancas`, `/entregas`, `/equipamentos`, `/relatorios`, `/admin/usuarios`, `/admin/config`) | Fechado via aliases + nova tela SSR |

## Conclusão
O projeto já possuía grande parte do fluxo em SSR FastAPI/Jinja2. Os gaps principais estavam em **normalização de URLs contratuais** e em alguns endpoints operacionais de entregas/timeline; estes foram implementados mantendo o stack existente e reaproveitando módulos atuais.
