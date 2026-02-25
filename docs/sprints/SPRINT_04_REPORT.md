# Sprint 04 — Relatório de Execução

## 1) O que foi feito
- Criado plano operacional da sprint em `docs/sprints/SPRINT_04_EXECUTION.md`.
- Implementada validação de CPF (normalização + dígitos verificadores) em `src/Domain/CpfValidator.php`.
- Implementado store de domínio social para famílias/dependentes/crianças em `src/Domain/SocialStore.php` com persistência em arquivo JSON para manter consistência entre requisições HTTP.
- Evoluído `src/Http/Kernel.php` com APIs de domínio da sprint:
  - `GET/POST /families`
  - `GET/PUT/DELETE /families/{id}`
  - `GET/POST /dependents`
  - `DELETE /dependents/{id}`
  - `GET/POST /children`
  - `DELETE /children/{id}`
- Implementadas validações de unicidade CPF e integridade de `family_id`.
- Implementada auditoria para operações cadastrais (`family.*`, `dependent.*`, `child.*`).
- Adicionado teste de integração da sprint em `tests/Feature/FamilyDomainCrudTest.php`.
- Atualizados checks em `scripts/ci_checks.sh` e README com endpoints da Sprint 04.

## 2) O que NÃO foi feito (e por quê)
- Não foi adicionada persistência em banco relacional nem migrações (fora do escopo desta sprint no plano incremental atual).
- Não foram criadas/alteradas telas (fora do escopo e controlado por `docs/SCREEN_RULES.md`).
- Não foi implementado catálogo completo de campos das entidades sociais; apenas o mínimo necessário para cumprir CRUD e validações centrais da sprint.

## 3) Evidências
- `bash scripts/ci_checks.sh` → OK.
- Teste `FamilyDomainCrudTest` valida:
  - criação de família com CPF válido;
  - rejeição de CPF inválido;
  - rejeição de CPF duplicado;
  - integridade de relacionamento para dependentes/crianças;
  - proteção de escrita para perfil leitura.
- Smoke HTTP manual:
  - login operador;
  - criação de família;
  - criação de dependente após família criada (status `201`).

## 4) Riscos e pendências
- Persistência em JSON é transitória para bootstrap e deve evoluir para persistência em banco na fase apropriada.
- Necessário expandir contratos de campos para maior paridade funcional com legado.
- Necessário versionar endpoints REST e alinhar adaptadores com matriz de compatibilidade da Sprint 01.

## 5) Próxima sprint — pré-requisitos
- Avançar para módulo de pessoas/ficha social + encaminhamentos + LGPD (Sprint 05) mantendo autenticação e auditoria.
- Definir estratégia de persistência definitiva dos módulos já migrados.

## 6) Checklist de conformidade
- [x] Respeitei `docs/DB_RULES_MYSQL.md` (sim — sem alteração de schema/migração).
- [x] Respeitei `docs/SCREEN_RULES.md` (sim — sem criação/alteração de telas).
- [x] Respeitei a Sprint 4 do plano (sim — CRUD famílias/dependentes/crianças + validações + integridade).
- [x] Não criei campos/tabelas/telas inventadas fora do escopo (sim).
- [x] Rodei testes/lint/build (sim). Comandos: `bash scripts/ci_checks.sh`; `php -S 127.0.0.1:8121 -t public` + `curl` de smoke para login/família/dependente.
