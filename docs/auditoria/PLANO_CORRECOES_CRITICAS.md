# Plano de Correções Críticas (Pós-auditoria)

## 1) Objetivo
Estabelecer backlog técnico priorizado para elevar o sistema de ~61% para aderência de produção à especificação oficial.

## 2) Itens críticos (não aplicados automaticamente)

| Prioridade | Item | Motivo crítico | Ação proposta | Critério de aceite |
|---|---|---|---|---|
| P0 | Hash de senha obrigatório | Violação direta de requisito de segurança DOCX | Migrar autenticação para `password_hash/password_verify` (bcrypt/argon2), remover senhas plaintext de bootstrap | Nenhuma senha em texto puro no runtime; login funcional com hash |
| P0 | Recuperação de senha com token/expiração | Requisito funcional obrigatório ausente | Implementar fluxo `/auth/forgot` + `/auth/reset` com token expirável e auditoria | Fluxo ponta-a-ponta com testes de validade/expiração |
| P0 | Modelo de dados social completo | Base atual insuficiente para fluxo oficial | Implementar migrations para `users`, `people`, `social_records`, `referrals`, `spiritual_followups`, `visits`, `audit_logs` conforme DOCX | Migrations aplicadas e validação de integridade/FKs |
| P0 | RBAC por perfil/módulo/ação | Conformidade de governança e LGPD | Criar matriz de permissões por perfil oficial (`admin`,`voluntario`,`pastoral`,`viewer`) com enforcement por rota/ação | Testes de autorização por perfil cobrindo módulos críticos |
| P1 | Módulo Visitas e Pendências | Lacuna operacional importante | Implementar API + tela de visitas pendentes/concluídas com vínculo família/pessoa | CRUD/fluxo funcional + alertas básicos |
| P1 | Dashboard operacional real | Indicadores e alertas exigidos em operação | Substituir stubs por consultas reais de indicadores/alertas | Cards e alertas alimentados por dados reais |
| P1 | Entregas com ticket sequencial | Regra de negócio oficial | Introduzir `ticket_number` sequencial por evento e imutabilidade após publicação | Testes garantindo sequência sem colisão e imutabilidade |
| P2 | Relatórios mensais completos | Prestação de contas institucional | Implementar consultas e exportações por período/bairro/status para todos módulos listados | Relatórios oficiais gerados em CSV/XLSX/PDF |
| P2 | Limpeza de legado com política | Reduz risco operacional | Definir política de retenção e remover/arquivar artefatos legacy fora de runtime | Inventário de legado aprovado e limpeza executada |

## 3) Dependências e ordem de execução sugerida
1. Segurança de autenticação (P0).
2. Expansão de schema e persistência (P0).
3. RBAC completo (P0).
4. Visitas + dashboard + entregas avançadas (P1).
5. Relatórios finais + limpeza de legado (P2).

## 4) Riscos e mitigação
- **Risco de regressão funcional:** mitigar com bateria de testes de contrato por endpoint.
- **Risco de migração de dados:** mitigar com scripts de reconciliação e dry-run em base clone.
- **Risco de conflito de requisito (DOCX/PDF):** mitigar aplicando ADR-0002 antes de mudanças de schema.

## 5) Conclusão
Sem execução deste plano, a recomendação técnica permanece **não liberar para produção**.


## 6) Execução aplicada (Sprint 21)

### Itens executados neste ciclo
- **P0 — Hash de senha obrigatório:** autenticação migrada para `password_hash/password_verify` com armazenamento em `password_hash` e sem campo de senha plaintext no bootstrap de usuários.
- **P0 — Recuperação de senha com token/expiração:** implementados endpoints `POST /auth/forgot` e `POST /auth/reset` com token de uso único, validade configurável e auditoria de solicitação/conclusão.
- **P0 — RBAC por perfil/módulo/ação (base):** padronizados perfis oficiais (`admin`, `voluntario`, `viewer`) e enforcement explícito no escopo administrativo (`admin.ping`) + escopo de escrita por perfis operacionais.
- **P0 — Modelo social completo (DDL inicial):** criada migration `004_create_social_official_core.sql` com tabelas `users`, `people`, `social_records`, `referrals`, `spiritual_followups`, `visits`, `audit_logs` e FKs.

### Evidências técnicas
- Código: `src/Auth/UserStore.php`, `src/Http/Kernel.php`.
- Contrato API: `docs/sprints/artifacts/openapi_php_v1.json`.
- Banco de dados: `database/migrations/004_create_social_official_core.sql`.
- Testes: `tests/Feature/AuthPasswordResetHashTest.php`.

### Pendências remanescentes para fechamento integral do plano
- Expandir enforcement RBAC para todas as rotas por **permissão por módulo/ação**, reduzindo dependência de checagem por perfil macro.
- Persistir fluxo de reset em storage transacional (atualmente em memória para bootstrap local).
- Implementar UI/fluxo operacional de visitas pendentes/concluídas e dashboard operacional com indicadores reais.
- Completar relatórios mensais oficiais em todos formatos e política de limpeza/retensão de legado.

## 7) Próximo passo executado (Sprint 22)

- **RBAC expandido para matriz por rota/módulo/ação**: adicionado resolver central de permissão no kernel (`families.*`, `street.*`, `delivery.*`, `equipment.*`, `reports.read`, `settings.*`, `eligibility.check`, `admin.ping`) com bloqueio `403` e trilha de auditoria quando houver violação.
- **Cobertura de teste**: atualizado teste de autenticação/RBAC para validar bloqueio de escrita para perfil `viewer` e leitura permitida em configurações.

> Observação: o enforcement de permissão foi aplicado no gateway HTTP atual, preservando compatibilidade com as validações de papel já existentes para rotas de escrita.

## 8) Próximo passo executado (Sprint 23)

- **Persistência durável no reset de senha:** fluxo `/auth/forgot` e `/auth/reset` migrado para armazenamento persistente de tokens (`AuthResetTokenStore`) com limpeza de expirados, consumo único e armazenamento por hash de token.
- **Qualidade de execução em testes:** testes de autenticação/RBAC e reset agora usam storage temporário isolado para evitar artefatos locais em `data/` durante a suíte.

> Resultado: pendência de “persistir fluxo de reset em storage transacional” foi parcialmente endereçada com persistência local durável; etapa futura recomendada é migrar o armazenamento para tabela relacional dedicada.

## 9) Próximo passo executado (Sprint 24)

- **Persistência transacional para reset de senha:** adicionada migration `005_create_auth_reset_tokens.sql` com tabela dedicada (`auth_reset_tokens`) para tokens de reset, expiração e marcação de consumo.
- **Store de reset com backend relacional opcional:** `AuthResetTokenStore` agora suporta driver `mysql` via `AUTH_RESET_TOKEN_STORE_DRIVER=mysql`, mantendo fallback JSON para ambientes locais.
- **Segurança de armazenamento:** persistência continua baseada em hash do token (`sha256`) e consumo de uso único.
- **Cobertura de teste do store:** novo teste `AuthResetTokenStoreTest` valida não persistir token plaintext, uso único e rejeição de token expirado.

> Resultado: pendência de evoluir reset para base transacional foi atendida com suporte relacional dedicado e compatibilidade retroativa.

## 10) Próximo passo executado (Sprint 25)

- **Módulo de Visitas e Pendências (P1):** implementados endpoints `GET /visits`, `POST /visits` e `POST /visits/{id}/complete` com fluxo pendente/concluída e vínculo por `person_id`/`family_id`.
- **Persistência no domínio social:** `SocialStore` passou a suportar visitas em JSON e em MySQL (`visits`), incluindo listagem com filtro por status e conclusão.
- **RBAC aplicado ao módulo de visitas:** matriz de permissões estendida para `visits.read` e `visits.write` por rota.
- **Contrato e testes:** OpenAPI atualizado e novo teste `VisitsModuleTest` cobrindo criação, listagem, conclusão e bloqueio de escrita para perfil de leitura.

## 11) Próximo passo executado (Sprint 26)

- **Entregas com ticket sequencial (P1):** convites em eventos de entrega agora recebem `ticket_number` sequencial por evento.
- **Imutabilidade após publicação:** implementado endpoint `POST /deliveries/events/{id}/publish`; após publicação, novos convites no evento retornam conflito de imutabilidade.
- **Persistência relacional:** criada migration `006_alter_delivery_invites_ticket_and_publish.sql` para `ticket_number` em `delivery_invites` e `published_at` em `delivery_events`.
- **Contrato e testes:** OpenAPI atualizado e `DeliveryEventsRulesTest` expandido para validar sequência de tickets e bloqueio pós-publicação.

## 12) Próximo passo executado (Sprint 27)

- **Dashboard operacional real (P1):** endpoint `GET /reports/summary` evoluído para retornar métricas operacionais reais adicionais (`pending_visits_total`, `published_events_total`) e lista de alertas acionáveis.
- **Alertas de operação:** incluídos alertas para visitas pendentes e empréstimos em aberto, com contagem agregada para priorização diária.
- **Validação automatizada:** `ReportsEligibilitySettingsTest` ampliado para garantir presença de métricas operacionais e estrutura de alertas no resumo.

## 13) Próximo passo executado (Sprint 28)

- **Relatórios mensais completos (P2, avanço):** adicionado endpoint `GET /reports/monthly` com período parametrizável (`YYYY-MM`) para consolidação mensal operacional.
- **Indicadores mensais no backend:** resumo mensal passa a agregar famílias, pessoas de rua, eventos de entrega no período, eventos publicados no período, visitas totais e visitas por status, além de empréstimos em aberto.
- **Contrato e qualidade:** OpenAPI e testes foram atualizados com validação de período inválido e consistência das métricas mensais.

## 14) Próximo passo executado (Sprint 29)

- **Relatórios mensais completos (P2, avanço adicional):** adicionado endpoint `GET /reports/monthly/export.csv` para exportação dos indicadores mensais em CSV.
- **Filtro operacional:** exportação suporta `period` (`YYYY-MM`) e filtro opcional `visit_status` para recorte por status de visitas.
- **Contrato e testes:** OpenAPI e contrato automatizado atualizados, com novo teste de exportação mensal validando sucesso e rejeição de parâmetros inválidos.

## 15) Próximo passo executado (Sprint 30)

- **Relatórios mensais completos (P2, formatos):** adicionados endpoints `GET /reports/monthly/export.xlsx` e `GET /reports/monthly/export.pdf`.
- **Padronização de métricas:** exportações mensal CSV/XLSX/PDF agora reutilizam o mesmo conjunto de métricas operacionais no backend.
- **Confiabilidade de contrato:** OpenAPI e testes de contrato atualizados para os novos formatos de exportação mensal.

## 16) Próximo passo executado (Sprint 31)

- **Limpeza de legado com política (P2):** definida política formal de retenção e limpeza em `docs/auditoria/POLITICA_RETENCAO_LEGADO.md`.
- **Inventário automatizado:** criado `scripts/legacy_cleanup_report.php` para inventariar caminhos legados e apoiar decisão de arquivamento/remoção.
- **Governança de execução:** incluído teste automatizado do relatório (`LegacyCleanupReportTest`) e integração na rotina de checks.
