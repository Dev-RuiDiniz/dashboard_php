# Sprint 16 — Runbook Final de Produção Assistida e Encerramento

## 1) Objetivo
Executar cutover assistido do backend PHP com risco controlado, validação técnica e capacidade de rollback imediato.

## 2) Pré-requisitos obrigatórios
- `bash scripts/ci_checks.sh` verde no commit candidato.
- Migrations aplicadas com sucesso: `php scripts/run_migrations.php`.
- (Se aplicável) carga de dados executada: `php scripts/migrate_json_to_mysql.php`.
- Variáveis de ambiente revisadas (`MYSQL_*`, `*_STORE_DRIVER`, `JWT_SECRET`).
- Observabilidade ativa (logs JSON e request_id).

## 3) Janela de cutover (checklist)
1. Congelar deploys concorrentes.
2. Snapshot/backup do banco.
3. Ativar modo de manutenção na aplicação legada (se necessário).
4. Executar release do backend PHP.
5. Executar smoke de endpoints críticos:
   - `GET /health`, `GET /ready`
   - `POST /auth/login`, `GET /me`
   - `GET /reports/summary`
   - `POST /eligibility/check`
6. Validar exports:
   - `/reports/export.csv`
   - `/reports/export.xlsx`
   - `/reports/export.pdf`

## 4) Reconciliação pós-cutover
- Conferir contagens mínimas por domínio (famílias, pessoas street, eventos, equipamentos).
- Validar amostra de CPFs e vínculos (`family_id`) entre domínios.
- Confirmar códigos de retirada e estados de empréstimo em amostra.

## 5) Critérios Go/No-Go
### Go
- Checks verdes.
- Smoke e reconciliação sem divergências críticas.
- Taxa de erro HTTP 5xx dentro do baseline esperado.

### No-Go
- Falha em autenticação básica.
- Divergência de dados crítica na reconciliação.
- Regressão severa de disponibilidade (`/ready` instável).

## 6) Rollback operacional
1. Redirecionar tráfego para versão anterior estável.
2. Reverter release da aplicação.
3. Restaurar backup se migração de dados tiver corrompido integridade.
4. Revalidar `GET /health`/`GET /ready` e smoke mínimo.
5. Abrir incidente com linha do tempo + causa raiz.

## 7) Encerramento da migração
- Registrar decisão Go/No-Go assinada por responsável técnico.
- Registrar evidências (checks, logs, reconciliação).
- Atualizar documento consolidado e marcar migração como encerrada.
