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

