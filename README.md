# Sistema Igreja Social (PHP + MySQL/MariaDB)

Sistema web de ação social para gestão de famílias em vulnerabilidade, pessoas em situação de rua, entregas de cestas, equipamentos de mobilidade, visitas e relatórios operacionais.

> Baseado na especificação oficial: `Especificacao_Sistema_Igreja_Social_PHP_MySQL.docx`.

---

## 1) O que o sistema faz

### 1.1 Autenticação e segurança
- Login com JWT (`POST /auth/login`).
- Perfil do usuário autenticado (`GET /me`).
- Logout lógico (`POST /auth/logout`).
- Recuperação de senha com token (`POST /auth/forgot`, `POST /auth/reset`).
- Proteções de segurança no entrypoint (headers de hardening e lockout por tentativas).

### 1.2 Gestão social (famílias, dependentes, crianças)
- Cadastro, listagem, edição e remoção de famílias.
- Cadastro de dependentes e crianças vinculadas à família.
- Regras de negócio como validação/bloqueio de CPF duplicado e integridade relacional de vínculos.

### 1.3 Pessoas acompanhadas (situação de rua) e encaminhamentos
- Cadastro e listagem de pessoas acompanhadas.
- Encaminhamentos com atualização de status.
- Regra LGPD/consentimento para conclusão de atendimento.

### 1.4 Entregas de cestas
- Cadastro e listagem de eventos de entrega.
- Convites por evento com código de retirada.
- Retirada com assinatura e bloqueio de duplicidade mensal por família.

### 1.5 Equipamentos de mobilidade
- Cadastro e edição de equipamentos.
- Empréstimo e devolução.
- Status operacional (`disponivel`, `emprestado`, `manutencao`).

### 1.6 Visitas sociais
- Listagem de visitas.
- Criação de solicitação de visita.
- Conclusão de visita (`/visits/{id}/complete`).

### 1.7 Relatórios e exportações
- Resumo operacional (`/reports/summary`).
- Relatório mensal (`/reports/monthly`).
- Exportações CSV, XLSX e PDF (resumo e mensal).

### 1.8 Configurações e elegibilidade
- Leitura/atualização de regras de elegibilidade (`/settings/eligibility`).
- Validação de elegibilidade (`/eligibility/check`).

---

## 2) Perfis, usuários iniciais e senhas padrão

> **Atenção:** usuários abaixo são bootstrap para ambiente inicial. Troque imediatamente em staging/prod.

| Perfil | E-mail | Senha inicial | Observação |
|---|---|---|---|
| Administrador | `admin@local` | `admin123` | Acesso total (`*`). |
| Voluntário/Operador | `operador@local` | `operador123` | Operação de módulos sociais. |
| Visualizador | `leitura@local` | `leitura123` | Leitura sem escrita. |

Permissões são aplicadas por rota/módulo (ex.: `families.read`, `delivery.write`, `reports.read`, `visits.write`).

---

## 3) Requisitos de ambiente

### 3.1 Versões recomendadas
- PHP **8.1+** (recomendado 8.2+).
- MySQL 8+ ou MariaDB compatível.

### 3.2 Extensões PHP
- `pdo`, `pdo_mysql`, `json`, `mbstring`, `openssl`, `fileinfo`.
- `zip` recomendada para cenários de exportação XLSX.

---

## 4) Configuração (.env / variáveis)

Variáveis principais:
- `APP_ENV` (`local`, `staging`, `production`)
- `APP_READY` (`true`/`false`)
- `JWT_SECRET` (**obrigatória em ambiente real**)
- `SOCIAL_STORE_DRIVER` (`json` ou `mysql`)
- `STREET_STORE_DRIVER` (`json` ou `mysql`)
- `DELIVERY_STORE_DRIVER` (`json` ou `mysql`)
- `EQUIPMENT_STORE_DRIVER` (`json` ou `mysql`)
- `SETTINGS_STORE_DRIVER` (`json` ou `mysql`)
- Banco:
  - `MYSQL_DSN` **ou**
  - `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_CHARSET`

Exemplo mínimo local:
```bash
export APP_ENV=local
export APP_READY=true
export JWT_SECRET='troque-isto-em-producao'
export SOCIAL_STORE_DRIVER=json
export STREET_STORE_DRIVER=json
export DELIVERY_STORE_DRIVER=json
export EQUIPMENT_STORE_DRIVER=json
export SETTINGS_STORE_DRIVER=json
```

---

## 5) Como subir localmente

### 5.1 Instalação
Este projeto não depende de framework pesado para subir o núcleo atual. Basta PHP + shell.

### 5.2 Executar testes/checks
```bash
bash scripts/ci_checks.sh
```

### 5.3 Subir servidor local
```bash
php -S 127.0.0.1:8099 -t public
```

### 5.4 Health e ready
```bash
curl -i http://127.0.0.1:8099/health
curl -i http://127.0.0.1:8099/ready
```

---

## 6) Fluxo rápido de uso (API)

### 6.1 Login
```bash
curl -s -X POST http://127.0.0.1:8099/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@local","password":"admin123"}'
```

Copie o `token` retornado.

### 6.2 Consultar usuário autenticado
```bash
curl -s http://127.0.0.1:8099/me \
  -H 'Authorization: Bearer SEU_TOKEN'
```

### 6.3 Criar família
```bash
curl -s -X POST http://127.0.0.1:8099/families \
  -H 'Authorization: Bearer SEU_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{"responsible_full_name":"Maria Silva","responsible_cpf":"529.982.247-25"}'
```

### 6.4 Criar visita
```bash
curl -s -X POST http://127.0.0.1:8099/visits \
  -H 'Authorization: Bearer SEU_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{"family_id":1,"notes":"Visita inicial"}'
```

### 6.5 Gerar relatório mensal
```bash
curl -s "http://127.0.0.1:8099/reports/monthly?period=2026-02" \
  -H 'Authorization: Bearer SEU_TOKEN'
```

---

## 7) Endpoints principais

### Sistema
- `GET /health`
- `GET /ready`

### Auth
- `POST /auth/login`
- `POST /auth/forgot`
- `POST /auth/reset`
- `POST /auth/logout`
- `GET /me`
- `GET /admin/ping`

### Famílias / Dependentes / Crianças
- `GET/POST /families`
- `GET/PUT/DELETE /families/{id}`
- `GET/POST /dependents`
- `DELETE /dependents/{id}`
- `GET/POST /children`
- `DELETE /children/{id}`

### Pessoas acompanhadas (street)
- `GET/POST /street/people`
- `POST /street/referrals`
- `POST /street/referrals/{id}/status`

### Entregas
- `GET/POST /deliveries/events`
- `POST /deliveries/events/{id}/invites`
- `POST /deliveries/events/{id}/withdrawals`

### Equipamentos
- `GET/POST /equipment`
- `PUT /equipment/{id}`
- `GET/POST /equipment/loans`
- `POST /equipment/loans/{id}/return`

### Visitas
- `GET/POST /visits`
- `POST /visits/{id}/complete`

### Relatórios
- `GET /reports/summary`
- `GET /reports/monthly`
- `GET /reports/export.csv`
- `GET /reports/export.xlsx`
- `GET /reports/export.pdf`
- `GET /reports/monthly/export.csv`
- `GET /reports/monthly/export.xlsx`
- `GET /reports/monthly/export.pdf`

### Configurações e elegibilidade
- `GET/PUT /settings/eligibility`
- `POST /eligibility/check`

---

## 8) Banco de dados e migração

### 8.1 Aplicar migrations
```bash
php scripts/run_migrations.php
```

### 8.2 Migrar dados legados JSON para MySQL
```bash
php scripts/migrate_json_to_mysql.php
```

### 8.3 Validar reconciliação e postura
```bash
php scripts/reconciliation_report.php
php scripts/security_posture_report.php
php scripts/pilot_cutover_dry_run.php
php scripts/handover_closure_report.php
```

---

## 9) Deploy na Hostinger (resumo prático)

1. Configurar domínio e HTTPS.
2. Publicar projeto com `document root` apontando para `public/`.
3. Definir variáveis de ambiente de produção.
4. Provisionar MySQL/MariaDB e executar migrations.
5. Rodar reconciliação e dry-run de cutover.
6. Fazer smoke test (`/health`, `/ready`, login, CRUDs críticos, relatórios).
7. Entrar em operação monitorada.

Checklist detalhado: `docs/auditoria/READY_FOR_PRODUCTION_CHECKLIST.md`.
Plano por prioridades (consolidação + envio para produção): `docs/auditoria/PLANO_CONSOLIDACAO_PRODUCAO_PRIORIDADES.md`.

---

## 10) Testes automatizados

Suites em `tests/Feature/` cobrem, entre outros:
- health/readiness,
- autenticação/RBAC/reset senha,
- famílias/dependentes/crianças,
- street/LGPD,
- entregas,
- equipamentos,
- visitas,
- relatórios e exportações,
- prontidão relacional e handover.

Rodar tudo:
```bash
bash scripts/ci_checks.sh
```

---

## 11) Estrutura de pastas (alto nível)

- `public/` — entrypoint HTTP.
- `src/Http/` — kernel e contexto de requisição.
- `src/Auth/` — JWT, usuários e reset.
- `src/Domain/` — regras de domínio e stores.
- `src/Reports/` — exportações/relatórios.
- `database/migrations/` — schema SQL incremental.
- `scripts/` — migração, reconciliação, segurança e handover.
- `tests/Feature/` — testes automatizados.
- `docs/` — documentação de sprints, auditoria e decisões.

---

## 12) Observações importantes para produção

- Troque imediatamente credenciais bootstrap.
- Mantenha `JWT_SECRET` forte e rotacionável.
- Ative somente drivers `mysql` em produção (evitar JSON como persistência principal).
- Defina rotina de backup e teste de restauração.
- Restrinja acesso ao `.env` e logs sensíveis.
