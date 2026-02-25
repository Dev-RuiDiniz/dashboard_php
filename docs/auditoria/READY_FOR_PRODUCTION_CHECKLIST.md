# Ready for Production Checklist

## 1) Versões mínimas recomendadas
- PHP: **8.2+** (DOCX permite 8.1+, recomenda 8.2).
- MySQL/MariaDB: **MySQL 8.0+** ou MariaDB compatível.
- Web server: Apache/Nginx apontando `document root` para `/public`.

## 2) Extensões PHP necessárias
- `pdo`
- `pdo_mysql`
- `json`
- `mbstring`
- `openssl`
- `fileinfo`
- `zip` (para exportações XLSX quando biblioteca real for aplicada)
- `gd`/`imagick` (opcional, conforme engine de PDF)

## 3) Variáveis de ambiente obrigatórias

### Runtime atual (repositório)
- `APP_ENV`
- `APP_READY`
- `JWT_SECRET`
- `SOCIAL_STORE_DRIVER`, `STREET_STORE_DRIVER`, `DELIVERY_STORE_DRIVER`, `EQUIPMENT_STORE_DRIVER`, `SETTINGS_STORE_DRIVER`
- `MYSQL_DSN` **ou** (`MYSQL_HOST`,`MYSQL_PORT`,`MYSQL_DATABASE`,`MYSQL_USER`,`MYSQL_PASSWORD`,`MYSQL_CHARSET`)

### Deploy DOCX
- `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASS`
- `APP_URL`, `APP_KEY`

## 4) Queue / Scheduler
- **Situação atual:** não há implementação formal de filas e scheduler no runtime principal.
- **Checklist obrigatório para produção:**
  - [ ] Definir mecanismo de job agendado para backup semanal (`mysqldump`) e rotinas de manutenção.
  - [ ] Definir monitoramento de falha de jobs.
  - [ ] Documentar retenção de backups e testes de restauração.

## 5) Storage e logs
- Diretórios críticos graváveis pelo usuário do servidor:
  - `storage/`
  - `storage/logs/`
  - `storage/exports/`
  - `storage/uploads/`
- Permissões recomendadas:
  - diretórios `775`
  - arquivos `664`

## 6) Permissões de pasta e segurança operacional
- [ ] `.env` fora de versionamento e sem permissões públicas.
- [ ] HTTPS obrigatório e redirect HTTP→HTTPS.
- [ ] Headers de segurança mantidos no entrypoint.
- [ ] Política de rotação de logs definida.

## 7) Índices críticos validados
- [ ] CPF (famílias e pessoas).
- [ ] FKs principais (`family_id`, `event_id`, `equipment_id`).
- [ ] Índices por data/status para entregas e empréstimos.
- [ ] Índices para filtros de listagem (bairro/cidade/status) após expansão de schema oficial.

## 8) Backup strategy
- Backup full semanal + incremental diário (ou full diário, conforme limite de Hostinger).
- Encriptação de backup em repouso.
- Armazenamento externo (não somente no mesmo host).
- Teste de restauração mensal documentado.

## 9) Plano de rollback
1. Snapshot do banco antes do deploy.
2. Tag de release no Git (`release-YYYYMMDD-HHMM`).
3. Deploy blue/green simplificado (ou diretório versionado com symlink atômico).
4. Em falha: restaurar snapshot + retornar tag anterior.
5. Executar smoke tests (`/health`, `/ready`, login, endpoints críticos).

## 10) Passo a passo de deploy (pré-produção → produção)
1. `git checkout <tag-release>`.
2. Provisionar `.env` de produção.
3. Validar extensões PHP e conectividade MySQL.
4. Executar migrations controladas (`php scripts/run_migrations.php`).
5. Executar reconciliação (`php scripts/reconciliation_report.php`).
6. Validar segurança (`php scripts/security_posture_report.php`).
7. Executar smoke tests automatizados (`bash scripts/ci_checks.sh`).
8. Publicar release e monitorar logs/erros por 24h.

## 11) Gate final de prontidão
- **Estado atual:** **NÃO PRONTO** para produção até fechamento dos itens críticos do plano de correções.

