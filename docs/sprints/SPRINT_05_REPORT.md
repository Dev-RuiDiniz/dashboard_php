# Sprint 05 — Relatório de Execução

## 1) O que foi feito
- Criado plano operacional da sprint em `docs/sprints/SPRINT_05_EXECUTION.md`.
- Implementado módulo social street com persistência bootstrap em arquivo JSON em `src/Domain/StreetStore.php`.
- Evoluído `src/Http/Kernel.php` com endpoints da Sprint 05:
  - `GET/POST /street/people`
  - `POST /street/referrals`
  - `POST /street/referrals/{id}/status`
- Implementada regra LGPD: atendimento concluído exige consentimento aceito e assinatura (`consent_accepted=true` e `signature_name` não vazio).
- Implementada auditoria de eventos críticos (`street.person.created`, `street.referral.created`, `street.referral.status_updated`).
- Adicionado teste de sprint em `tests/Feature/StreetLgpdReferralTest.php`.
- Atualizados `public/index.php`, `scripts/ci_checks.sh` e `README.md` para incluir o novo domínio.

## 2) O que NÃO foi feito (e por quê)
- Não houve criação/alteração de telas (fora do escopo da sprint e regido por `docs/SCREEN_RULES.md`).
- Não houve alterações de schema/migrações de banco (fora do escopo desta etapa incremental).
- Não foi implementada cobertura completa de todos os campos sociais do legado, apenas o mínimo para cumprimento da Sprint 05.

## 3) Evidências
- `bash scripts/ci_checks.sh` → OK (todas as suítes feature passam).
- Smoke HTTP manual:
  - `POST /street/people` concluído sem consentimento retorna `422`.
  - `POST /street/referrals/{id}/status` retorna `200`.

## 4) Riscos e pendências
- Persistência em JSON é temporária e deve ser substituída por persistência definitiva na evolução da migração.
- Campos de evidência jurídica LGPD ainda estão simplificados no bootstrap e precisarão aprofundamento para paridade completa.
- Contratos de API ainda necessitam versionamento/compatibilidade plena com matriz da Sprint 01.

## 5) Próxima sprint — pré-requisitos
- Avançar para Sprint 06 (entregas/eventos + regras críticas) mantendo trilha de auditoria e guardas RBAC.
- Planejar estratégia de persistência definitiva para módulos migrados.

## 6) Checklist de conformidade
- [x] Respeitei `docs/DB_RULES_MYSQL.md` (sim — sem mudança de schema/migração).
- [x] Respeitei `docs/SCREEN_RULES.md` (sim — sem novas telas/fluxos).
- [x] Respeitei a Sprint 05 do plano (sim — street + encaminhamentos + LGPD inicial).
- [x] Não criei campos/tabelas/telas inventadas fora do escopo (sim).
- [x] Rodei testes/lint/build (sim). Comandos: `bash scripts/ci_checks.sh`; `php -S 127.0.0.1:8130 -t public` + `curl` para endpoints street.
