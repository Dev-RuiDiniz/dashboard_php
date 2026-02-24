# CONTRATO_TELAS_ENDPOINTS

| Módulo | Tela/URL | Ação | Endpoint | Método | Payload | Status | Observações |
|---|---|---|---|---|---|---|---|
| 1. Auth | `/login` | autenticar (SSR) | `/login` | POST | form `email,password` | ✅ | cookie JWT |
| 1. Auth | API login | autenticar (API) | `/auth/login` | POST | json `email/username,password` | ✅ | novo endpoint |
| 1. Auth | `/password/forgot` | solicitar reset | `/password/forgot` | POST | form `email` | ✅ | link dev em ambiente não-prod |
| 1. Auth | `/password/reset` | redefinir senha | `/password/reset` | POST | form `token,password` | ✅ | token com expiração |
| 2. Dashboard | `/dashboard` | resumo operacional | `/dashboard` | GET | query opcionais | ✅ | SSR |
| 3. Famílias | `/familias` | listar + filtros | `/familias` | GET | query `name,cpf,...` | ✅ | chips/alertas de pendência |
| 3. Famílias | `/familias/nova/step/{n}` | wizard draft | `/familias/nova/step/{n}` | GET/POST | form | ✅ | etapas A/B/C/D |
| 3. Famílias | `/familias/{id}` | detalhe abas | `/familias/{id}` | GET | - | ✅ | resumo, dependentes, cestas, visitas |
| 3. Famílias | botão PDF | export ficha | `/familias/{id}/export.pdf` | GET | - | ✅ | PDF |
| 4. Pessoas | `/pessoas` | abrir módulo | `/pessoas` | GET | - | ✅ | alias -> `/rua` |
| 4. Pessoas | `/rua` | lista | `/rua` | GET | query | ✅ | fluxo atual de ficha social |
| 4. Pessoas | novo atendimento | registrar atendimento | `/rua/{id}/atendimentos` | POST | form | ✅ | inclui consentimento |
| 4. Pessoas | encaminhamento | criar | `/rua/{id}/encaminhamentos` | POST | form | ✅ | status controlado |
| 4. Pessoas | PDF individual | export | `/pessoas/{id}/export.pdf` | GET | - | ✅ | PDF |
| 5. Crianças | `/criancas` | listar | `/criancas` | GET | filtros | ✅ | SSR |
| 5. Crianças | `/criancas/nova` | criar | `/criancas` | POST | form | ✅ | valida família obrigatória |
| 5. Crianças | `/criancas/{id}/edit` | editar | `/criancas/{id}` | POST | form | ✅ | stack SSR |
| 6. Entregas | `/entregas` | painel de eventos | `/entregas` | GET | - | ✅ | novo |
| 6. Entregas | eventos | listar | `/entregas/eventos` | GET | - | ✅ | novo |
| 6. Entregas | criar evento | criar | `/entregas/eventos` | POST | json | ✅ | com `has_children_list` |
| 6. Entregas | convidar | manual/automático | `/entregas/eventos/{id}/convidar` | POST | json `mode,family_ids` | ✅ | critérios via elegibilidade |
| 6. Entregas | operação retirada | confirmar | `/entregas/eventos/{id}/retirada/{family_id}` | POST | json assinatura | ✅ | bloqueia duplicidade |
| 6. Entregas | encerrar evento | close | `/entregas/eventos/{id}/close` | POST | json opcional | ✅ | novo |
| 6. Entregas | exports | PDF/CSV/XLSX | `/entregas/eventos/{id}/export.*` | GET | - | ✅ | completo |
| 6. Entregas | lista crianças evento | visualizar/export | `/entregas/eventos/{id}/criancas*` | GET | - | ✅ | html/pdf/xlsx |
| 7. Equipamentos | `/equipamentos` | listar | `/equipamentos` | GET | filtros | ✅ | SSR |
| 7. Equipamentos | cadastro | criar/editar | `/equipamentos/novo`, `/equipamentos/{id}/editar` | GET/POST | form | ✅ | |
| 7. Equipamentos | empréstimo/devolução | operar | `/equipamentos/{id}/emprestimo`, `/equipamentos/{id}/devolver` | POST | form | ✅ | |
| 8. Relatórios | `/relatorios` | tela mensal | `/relatorios` | GET | `month,year,type` | ✅ | SSR |
| 8. Relatórios | export | PDF/CSV/XLSX | `/relatorios/*.pdf|csv|xlsx` | GET | query | ✅ | |
| 9. Admin | `/admin/usuarios` | listar usuários | `/admin/usuarios` | GET | - | ✅ | alias -> `/admin/users` |
| 9. Admin | `/admin/users` | CRUD básico | `/admin/users*` | GET/POST | form | ✅ | RBAC admin |
| 9. Admin | `/admin/config` | parâmetros | `/admin/config` | GET/POST | form | ✅ | |
| 10. UX extra | barra topo | busca global | `/busca` | GET | query `q` | ✅ | resultados mistos |
| 10. UX extra | agregador timeline | timeline | `/timeline` | GET | `family_id` ou `person_id` | ✅ | novo endpoint |
