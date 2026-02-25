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
