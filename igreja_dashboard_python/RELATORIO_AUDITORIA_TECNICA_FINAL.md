# RELATÓRIO DE AUDITORIA TÉCNICA FINAL — Sprint 10

Data: 2026-02-18
Sistema: Gestão da Ação Social — Primeira Igreja Batista de Taubaté

## 1) Inventário da stack real

- Backend: FastAPI
- Frontend: SSR com Jinja2 + Bootstrap
- ORM: SQLAlchemy 2.x
- Migrações: Alembic
- Banco: SQLite (local padrão) e suporte PostgreSQL
- Autenticação: JWT em cookie HTTPOnly
- Autorização: RBAC (`Admin`, `Operador`, `Leitura`)
- Relatórios: CSV/XLSX/PDF (motor PDF central)

## 2) Endpoints principais auditados

- Autenticação e segurança:
  - `GET/POST /login`
  - `GET/POST /password/forgot`
  - `GET/POST /password/reset`
  - `GET /logout`
- Administração e governança:
  - `GET/POST /admin/users*`
  - `GET/POST /admin/config`
  - `GET/POST /admin/consentimento`
  - `GET /admin/audit`
  - `GET/POST /admin/fechamento*`
- Operação social:
  - `GET/POST /familias*`
  - `GET/POST /criancas*`
  - `GET/POST /entregas/eventos*`
  - `GET/POST /equipamentos*`
  - `GET/POST /rua*`
- Relatórios:
  - `GET /relatorios/*`
  - PDFs de ficha/evento/oficial e download de artefatos
- Histórico:
  - `GET /historico*`
  - `GET /api/historico/series`

## 3) Checklist automatizado (script)

Script criado: `scripts/auditoria_tecnica_final.sh`.

### 3.1 Dependências
- `pip check`: **OK** (sem conflito de dependências).
- Pinagem: projeto usa limites mínimos (`>=`), **não há pinagem estrita total**; risco moderado para reprodutibilidade.

### 3.2 Configurações de ambiente críticas
- `DATABASE_URL`: presente
- `SECRET_KEY`: presente (obrigatória em produção)
- `COOKIE_SECURE`: presente
- `REPORTS_DIR`: presente

### 3.3 Migrações Alembic
- SQLite do zero até `head`: **OK**.
- `alembic check` SQLite: **WARN** (drift detectado em FKs de `monthly_closures`).
- PostgreSQL local: **WARN** (indisponível no ambiente atual — conexão recusada em `127.0.0.1:5432`).

### 3.4 Logs estruturados e proteção de PII
- Logs JSON estruturados habilitáveis (`LOG_JSON`).
- Sanitização de payload de auditoria remove campos sensíveis (`password`, `token`, etc.) e mascara CPF.
- Achado: ação de criação de pessoa em situação de rua registra `cpf` no `after` antes de sanitização (fica mascarado no payload persistido, mas manter monitoramento).

### 3.5 Rate-limit e lockout de login
- Rate-limit de login ativo com tabela de buckets (`rate_limit_events`).
- Lockout ativo por tentativas inválidas (`login_attempts`) com janela e limiar configuráveis.

### 3.6 Reset de senha seguro
- Token gerado com alta entropia (`secrets.token_urlsafe(48)`).
- Persistência por hash (`token_hash`).
- Expiração por TTL configurável.
- Uso único com campo `used_at`.

## 4) Configuração por ambiente

### Dev
- SQLite local padrão
- `COOKIE_SECURE=false` (override permitido)
- Link de reset exibido fora de produção

### Staging
- Recomendado PostgreSQL
- `SECRET_KEY` forte obrigatória
- `COOKIE_SECURE=true`
- diretório de relatórios persistente via `REPORTS_DIR`

### Produção
- PostgreSQL obrigatório
- `SECRET_KEY` obrigatória e rotacionável
- cookies `Secure`
- backup periódico + restore testado
- `ADMIN_OVERRIDE=false` por padrão

## 5) Riscos e mitigação

1. **Drift do `alembic check`**
   - Mitigação: corrigir metadata/migração de FKs em `monthly_closures`.
2. **Sem validação local de Postgres neste ambiente**
   - Mitigação: executar pipeline em staging com Postgres provisionado.
3. **Dependências sem pinagem exata**
   - Mitigação: opcionalmente adotar lockfile para releases institucionais.

## 6) Checklist de pronto para produção

- [x] Testes automatizados verdes.
- [x] Cobertura coletada com relatório.
- [x] Segurança de login/reset validada.
- [x] Consentimento e auditoria presentes.
- [x] Fechamento mensal, oficialização e hash SHA256 operacionais.
- [ ] `alembic check` sem drift (pendência técnica).
- [ ] Execução local Postgres comprovada neste ambiente (limitação de infraestrutura).

## 7) Conclusão

Sistema **apto para homologação institucional**, com duas pendências não bloqueantes para hardening operacional:
(1) ajuste de drift Alembic em SQLite check; (2) validação completa em staging PostgreSQL.
