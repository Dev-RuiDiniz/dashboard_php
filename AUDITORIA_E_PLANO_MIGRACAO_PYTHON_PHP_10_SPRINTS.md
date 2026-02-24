# Auditoria Técnica + Plano de Migração Python → PHP (10 Sprints)

## 1) Resumo executivo

O backend atual é uma aplicação **FastAPI + SQLAlchemy + Alembic** com abordagem híbrida (**SSR em Jinja2** e **endpoints JSON**), cobrindo os domínios principais do escopo social: autenticação/RBAC, famílias/dependentes/crianças, pessoas em situação de rua, eventos de entrega, equipamentos/empréstimos, relatórios e fechamento mensal.

A análise identifica que o repositório já possui boa cobertura de regras críticas (CPF único, bloqueio de duplicidade de retirada, LGPD com termo ativo, trilha de auditoria, rate limit + lockout), mas também apresenta riscos de migração por:

- concentração de regras e rotas em `app/main.py` (arquivo monolítico),
- coexistência de rotas HTML e API na mesma base,
- contratos não explicitamente versionados,
- geração de PDF/XLSX artesanal (sem biblioteca dedicada),
- ausência de tracing e de baseline formal de SLO/alertas.

A recomendação alvo é migrar para **Laravel 11 + PostgreSQL + JWT (tymon/jwt-auth ou Sanctum com token JWT customizado) + Spatie Permission + OpenTelemetry + logs JSON**, com migração incremental em 10 sprints e matriz de compatibilidade para preservar o contrato consumido pelo frontend React.

---

## 2) Achados da auditoria (com evidências por arquivo)

## 2.1 Inventário técnico

**Stack Python detectada**

- Framework HTTP: FastAPI (`app/main.py`, routers em `app/*/routes.py`).
- ORM: SQLAlchemy 2.x (`app/models/*.py`).
- Migrações: Alembic (`alembic/versions/*.py`).
- Auth: JWT com `python-jose`, senhas com `passlib` e fallback bcrypt (`app/core/security.py`).
- Templates SSR: Jinja2 (`templates/*`, `Jinja2Templates` em múltiplos routers).
- Exportações:
  - CSV/XLSX: gerador próprio em `app/reports/exporters.py`.
  - PDF: engine própria em `app/pdf/report_engine.py`.
- Dependências declaradas: `pyproject.toml`, `requirements.txt`.

**Estrutura de pastas relevante**

- `app/main.py`: boot, middleware, rotas SSR/API centrais.
- `app/models/`: entidades de domínio e segurança.
- `app/deliveries/routes.py`: eventos, convites, retiradas, exportações.
- `app/reports/routes.py`: relatórios e exportações.
- `app/closures/routes.py`: fechamento mensal.
- `app/eligibility/engine.py`: regras de elegibilidade/alertas.
- `app/security/rate_limit.py`: proteção de login.
- `app/services/audit.py`: auditoria de ações.

**Banco e migrações**

- DB primário: PostgreSQL (com fallback SQLite local), controlado por `DATABASE_URL`.
- Suporte a schemas lógicos (`auth`, `domain`) quando não SQLite (`app/db/schemas.py`).
- Histórico de migrações até `0016_pdf_aderencia_campos_regras.py`.

---

## 2.2 Mapa de API/rotas por módulo

> Fonte principal: varredura de decorators `@app.*` / `@router.*`.

## Autenticação e sessão

- `GET /login` (form SSR)
- `POST /login` (autentica + cookie)
- `POST /auth/login` (API JSON JWT)
- `GET /logout`
- `GET/POST /password/forgot`
- `GET/POST /password/reset`
- `GET /me` (perfil atual)

## Usuários/Config/Auditoria

- `GET /admin/users`, `GET /admin/usuarios` (alias)
- `GET/POST /admin/users/new`
- `GET/POST /admin/users/{user_id}/edit`
- `GET/POST /admin/config`
- `GET/POST /admin/consentimento`
- `GET /admin/audit`

## Famílias, dependentes, crianças, visitas

- `GET /familias`, `GET /familias/nova`, `GET/POST /familias/nova/step/{step}`
- `POST /familias/nova`
- `GET /familias/{family_id}`, `GET/POST /familias/{family_id}/editar`
- `POST /familias/{family_id}/inativar`
- `GET/POST /familias/{family_id}/dependentes/novo`
- `GET/POST /familias/{family_id}/dependentes/{dependent_id}/editar`
- `POST /familias/{family_id}/dependentes/{dependent_id}/remover`
- `POST /familias/{family_id}/cestas`
- `POST /familias/{family_id}/cestas/{basket_id}/editar`
- `POST /familias/{family_id}/cestas/{basket_id}/remover`
- `POST /familias/{family_id}/visitas`
- `POST /familias/{family_id}/visitas/{visit_request_id}/executar`
- `GET /familias/{family_id}/export.pdf`
- `GET /criancas`, `GET /criancas/nova`, `POST /criancas`
- `GET /criancas/{child_id}`, `GET/POST /criancas/{child_id}`, `POST /criancas/{child_id}/delete`

## Entregas/eventos/listas

Prefixo ` /entregas `:

- `POST /entregas/eventos`
- `GET /entregas/eventos`
- `POST /entregas/eventos/{event_id}/convidar`
- `POST /entregas/eventos/{event_id}/retirada/{family_id}`
- `POST /entregas/eventos/{event_id}/close`
- `GET /entregas/eventos/{event_id}/export.csv`
- `GET /entregas/eventos/{event_id}/export.xlsx`
- `GET /entregas/eventos/{event_id}/export.pdf`
- `GET /entregas/eventos/{event_id}/criancas`
- `GET /entregas/eventos/{event_id}/criancas/export.xlsx`
- `GET /entregas/eventos/{event_id}/criancas/export.pdf`

## Equipamentos/empréstimos

- `GET /equipamentos`, `GET /equipamentos/novo`, `POST /equipamentos/novo`
- `GET /equipamentos/{equipment_id}`
- `GET/POST /equipamentos/{equipment_id}/editar`
- `GET/POST /equipamentos/{equipment_id}/emprestimo`
- `POST /equipamentos/{equipment_id}/devolver`

## Rua/ficha social/encaminhamentos

- `GET /rua`, `GET /rua/nova`, `POST /rua/nova`
- `GET /rua/{person_id}`
- `POST /rua/{person_id}/atendimentos`
- `POST /rua/{person_id}/encaminhamentos`
- `POST /rua/encaminhamentos/{referral_id}/status`
- `GET /pessoas/{person_id}/export.pdf`

## Relatórios gerenciais

Prefixo `/relatorios`:

- `GET /relatorios`
- `GET /relatorios/export.csv`
- `GET /relatorios/export.xlsx`
- PDFs: `/familias.pdf`, `/cestas.pdf`, `/criancas.pdf`, `/encaminhamentos.pdf`, `/equipamentos.pdf`, `/pendencias.pdf`

## Fechamento mensal e histórico

- Prefixo `/fechamentos`:
  - `GET /fechamentos`
  - `POST /fechamentos/close`
  - `POST /fechamentos/reopen`
  - `POST /fechamentos/{year}/{month}/gerar-relatorio-oficial`
  - `GET /fechamentos/{year}/{month}/pdf`
  - `GET /fechamentos/{year}/{month}/relatorio-oficial.pdf`
  - `GET /fechamentos/{year}/{month}/snapshot.json`
  - `GET /fechamentos/{year}/{month}/relatorio-oficial.snapshot.json`
- Histórico:
  - `GET /historico`
  - `GET /historico/{year}/{month}`
  - `GET /api/historico/series`
  - `GET /historico/{year}/{month}/snapshot.json`

**Inconsistências notáveis de contrato**

- Mistura de endpoints SSR e API no mesmo namespace (ex.: `/login` HTML e `/auth/login` JSON).
- Rotas sem versionamento explícito (`/api/v1` ausente, exceto casos pontuais `/api/cep`, `/api/historico/series`).
- Alias legados (`/admin/usuarios`) coexistem com rotas principais.

---

## 2.3 Regras de negócio essenciais localizadas

## CPF único / validação / duplicidade

- `Family.responsible_cpf` é `unique=True`.
- `Dependent.cpf` e `StreetPerson.cpf` também têm unicidade.
- Fluxos de criação/edição normalizam e validam CPF em handlers utilitários de `app/main.py`.

## Bloqueio de duplicidade mensal em entregas

- `FoodBasket` possui unique constraint `uq_food_basket_family_month` (`family_id`, `reference_year`, `reference_month`).
- Em eventos, retirada duplicada é bloqueada por validação e por `IntegrityError` com resposta `409`.
- Elegibilidade considera limite mensal e janela desde última entrega (`app/eligibility/engine.py`, `SystemSettings`).

## Senha automática por evento

- Convites de evento geram `withdrawal_code` pseudoaleatório único (6 chars alfanuméricos).

## Presença / retirada / assinatura digital simples

- `DeliveryWithdrawal` exige `signature_accepted=True` para confirmação.
- Nome de assinatura (`signature_name`) e observações são persistidos.

## Perfis e permissões por módulo (RBAC)

- Papéis padrão: `Admin`, `Operador`, `Leitura` com matriz de permissões (`ROLE_DEFINITIONS`).
- Guards por rota com `require_roles` / `require_permissions`.

## Elegibilidade e alertas parametrizáveis

- Regras dependentes de `SystemSettings`:
  - limite de entregas no mês,
  - meses mínimos desde última entrega,
  - vulnerabilidade mínima,
  - obrigatoriedade de documentação.

---

## 2.4 Exportações e documentos

- CSV/XLSX: utilitários internos (`build_csv`, `build_xlsx`) sem dependência de pacote externo específico para Excel.
- PDF: gerador próprio em baixo nível (`report_engine.py`), usado por relatórios, famílias, eventos e fechamento.
- Templates HTML para telas e impressão em `templates/`.

**Risco técnico**: fidelidade visual de PDFs pode variar na migração por ausência de engine declarativa (wkhtmltopdf/dompdf/mpdf) e por implementação artesanal atual.

---

## 2.5 Segurança e LGPD

**Senha/hash**

- Hash principal: `pbkdf2_sha256` (Passlib), com fallback de verificação bcrypt legado.

**JWT**

- Algoritmo HS256, claim principal `sub`, expiração por configuração.
- Sem refresh token explícito no backend atual.

**Rate limit / bloqueio de tentativas**

- Limitação por IP/rota em janela deslizante.
- Lockout por tentativas falhas (identidade + IP e por usuário), com erro 429.

**Auditoria / trilha de ações**

- Entidade `AuditLog` + serviço `log_action` em operações sensíveis.
- Sanitização de payload com mascaramento de CPF e remoção de chaves sensíveis.

**LGPD / consentimento digital**

- Entidade `ConsentTerm` ativa.
- Campos de consentimento em famílias e pessoas de rua (`consent_term_version`, `consent_accepted_at`, `consent_accepted_by_user_id`, flag e assinatura quando aplicável).

**Observabilidade já existente**

- Middleware inclui `request_id`, duração, status, user_id em log.
- Formato JSON configurável no logger.

---

## 2.6 Riscos, débito técnico e pontos de atenção

1. **Monolito de rotas** em `app/main.py` aumenta risco de regressão e dificulta migração por domínio.
2. **Contratos API não formalizados** em OpenAPI versionado e sem consumer-contract tests.
3. **SSR + API acoplados** exigem decisão clara na migração (manter SSR em paralelo ou separar BFF/API pura).
4. **Exports artesanais** podem comprometer manutenção e compatibilidade visual no PHP.
5. **Sem tracing distribuído e SLO formal**; observabilidade parcial.
6. **Sem estratégia explícita de data migration idempotente** documentada por domínio.

---

## 3) Gap analysis vs escopo consolidado

| Requisito do escopo | Status no repo | Evidência resumida | Ação recomendada |
|---|---|---|---|
| Autenticação + perfis + permissões | **OK** | JWT, RBAC, guards por permissão/role | Manter matriz de permissões idêntica no PHP |
| Famílias + pessoas/ficha social | **OK/Parcial** | CRUD robusto, mas contratos misturam SSR/API | Extrair contratos REST explícitos e versionar |
| Crianças | **OK** | CRUD + exportações vinculadas a eventos | Garantir parity de validações e filtros |
| Entregas/eventos/listas | **OK** | Convite, retirada, bloqueios, exportações | Reproduzir regras de duplicidade e assinatura |
| Equipamentos/empréstimos | **OK** | CRUD + empréstimo/devolução/histórico | Incluir testes de concorrência/estado |
| Relatórios gerenciais | **Parcial** | Muitos relatórios, porém sem SLO/telemetria robusta | Definir performance budget + caching |
| Elegibilidade/alertas | **OK/Parcial** | Engine parametrizada existe | Expor gestão de regras com auditoria forte |
| LGPD consentimento digital | **OK** | termo ativo e rastros de aceite | Reforçar trilha de evidência jurídica |
| Rastreabilidade total (auditoria) | **Parcial** | AuditLog amplo, mas cobertura não é 100% garantida por política | Adotar interceptors/observers globais |
| Compatibilidade React via REST | **Parcial** | existem endpoints API, porém não padronizados/versionados | Criar matriz de contrato e gateway de compatibilidade |

---

## 4) Arquitetura alvo em PHP (proposta)

## 4.1 Framework e fundamentos

**Recomendação: Laravel 11 (PHP 8.3)**

Motivos:

- produtividade alta para CRUD complexo e validações;
- ecossistema maduro para auth, fila, cache, observabilidade;
- migrations/seeders robustos;
- facilidade de padronizar DTO/Resource/Policies;
- boa integração com PostgreSQL e ferramentas de auditoria.

## 4.2 Camadas e organização alvo

- `app/Domain/<Modulo>`: entidades, regras de domínio.
- `app/Application/<Modulo>`: casos de uso/services.
- `app/Http/Controllers/Api/V1`: endpoints REST versionados.
- `app/Http/Requests`: validações.
- `app/Http/Resources`: serialização estável.
- `app/Infrastructure/Persistence`: repositories e queries otimizadas.
- `database/migrations` + `database/seeders`.

## 4.3 Auth + RBAC

- JWT stateless para compatibilidade com frontend React.
- Policies + Gates + `spatie/laravel-permission`.
- Matriz de permissões espelhando `ROLE_DEFINITIONS` atual.

## 4.4 ORM e migrações

- Eloquent como padrão.
- Constraints e índices reproduzidos 1:1 (incluindo unique mensal, FKs e índices de auditoria).
- Estratégia de migração em duas fases:
  1) schema parity,
  2) data migration incremental e validada.

## 4.5 Exportações

- CSV: nativo + stream response.
- Excel: `maatwebsite/excel`.
- PDF: `barryvdh/laravel-dompdf` (ou Snappy/wkhtmltopdf para maior fidelidade de layout).
- Layouts “modelo fiel”: snapshots visuais aprovados por QA.

## 4.6 Config/secrets

- `.env` + secret manager (Vault/SSM/GCP Secret Manager).
- Chaves JWT rotacionáveis e segregadas por ambiente.

## 4.7 Logs e correlação

- Monolog JSON + middleware de `X-Request-ID`.
- Campos mínimos: `request_id`, `user_id`, `module`, `action`, `duration_ms`, `status_code`.

## 4.8 Estratégia de compatibilidade de API

- Introduzir `/api/v1` no PHP.
- Manter facade de compatibilidade para rotas legadas críticas até frontend migrar.
- Contratos formalizados em OpenAPI + testes de contrato (Pact/Schemathesis).

---

## 5) Matriz de compatibilidade de API (Python atual → PHP alvo)

| Domínio | Python atual | PHP alvo | Compatibilidade |
|---|---|---|---|
| Login API | `POST /auth/login` | `POST /api/v1/auth/login` + alias legado | **Alias obrigatório** |
| Perfil atual | `GET /me` | `GET /api/v1/auth/me` + alias `/me` | **Alias obrigatório** |
| Famílias | rotas SSR + posts form | REST `/api/v1/families` | **Adaptador necessário** |
| Crianças | misto SSR/POST | REST `/api/v1/children` | **Adaptador necessário** |
| Entregas/eventos | `/entregas/eventos/*` | `/api/v1/deliveries/events/*` + rewrite | **Mapeamento com rewrite** |
| Relatórios export | `/relatorios/export.*` | `/api/v1/reports/export.*` | **Header e payload equivalentes** |
| Equipamentos | `/equipamentos/*` | `/api/v1/equipment/*` | **Mapeamento de status/enum** |
| Rua/encaminhamentos | `/rua/*` | `/api/v1/street/*` | **Mapeamento de enums** |
| Fechamentos | `/fechamentos/*` | `/api/v1/closures/*` | **Paridade total de regras** |

**Diretriz**: durante transição, responder com o mesmo shape JSON legado quando rota antiga for chamada.

---

## 6) Plano de Migração em 10 Sprints

## Sprint 1 — Auditoria completa, baseline e compatibilidade

- **Objetivo**: fechar inventário técnico e contratos “as-is”.
- **Backlog**:
  - congelar mapa de endpoints e entidades;
  - gerar OpenAPI legado;
  - definir matriz de compatibilidade e riscos.
- **Critérios de aceite**:
  - inventário aprovado por produto/tech lead;
  - gaps classificados (OK/Parcial/Ausente/Divergente).
- **Testes**: smoke no backend atual + snapshot de contratos.
- **Observabilidade**: baseline de erro/latência atual (p95).
- **Entregáveis**: relatório de auditoria + backlog priorizado.
- **Riscos/Mitigação**: endpoint órfão → ativar rastreio de uso via logs de acesso.

## Sprint 2 — Setup PHP + CI + logs + healthchecks

- **Objetivo**: fundação da plataforma Laravel.
- **Backlog**:
  - bootstrap Laravel 11;
  - pipeline CI (lint, tests, security scan);
  - middleware `request_id`;
  - `/health` e `/ready`.
- **Aceite**: build verde, deploy em ambiente de dev/stage.
- **Testes**: unitários de infra + integração DB.
- **Observabilidade**: logs JSON padronizados.
- **Entregáveis**: repo PHP inicial + runbook de ambiente.
- **Risco**: divergência de ambiente → usar Docker Compose padronizado.

## Sprint 3 — Auth + usuários + RBAC + auditoria

- **Objetivo**: reproduzir segurança central.
- **Backlog**:
  - JWT login/me/logout;
  - usuários, roles e permissions;
  - trilha de auditoria para CRUD de usuários.
- **Aceite**: paridade funcional com fluxos atuais.
- **Testes**: unit (auth), integração (RBAC), contrato (`/auth/login`, `/me`).
- **Observabilidade**: métricas de falha de login + lockout.
- **Entregáveis**: módulo auth pronto em staging.
- **Risco**: quebra de sessão frontend → manter aliases legados.

## Sprint 4 — Famílias + membros + crianças

- **Objetivo**: domínio base social.
- **Backlog**:
  - CRUD famílias/dependentes/crianças;
  - validações CPF/documentos;
  - constraints de integridade.
- **Aceite**: regras de unicidade e consistência replicadas.
- **Testes**: unit validação CPF, integração CRUD, contrato endpoints críticos.
- **Observabilidade**: auditoria de alterações cadastrais.
- **Entregáveis**: APIs `/families`, `/dependents`, `/children`.
- **Risco**: diferenças de normalização CPF → testes de regressão com massa real anonimizada.

## Sprint 5 — Pessoas/ficha social + encaminhamentos + LGPD

- **Objetivo**: cobertura do módulo de rua e consentimento.
- **Backlog**:
  - CRUD street person e serviços;
  - fluxo de encaminhamento/status;
  - consentimento digital com evidências.
- **Aceite**: aceite LGPD obrigatório quando exigido.
- **Testes**: integração de fluxos ponta a ponta.
- **Observabilidade**: trilhas de consentimento e alteração de status.
- **Entregáveis**: módulo social street + documentos de compliance.
- **Risco**: lacuna jurídica de evidência → campos imutáveis de aceite + hash de versão do termo.

## Sprint 6 — Entregas/eventos + regras críticas

- **Objetivo**: migrar núcleo de distribuição.
- **Backlog**:
  - eventos, convites, retirada;
  - bloqueio duplicidade por mês/evento;
  - senha automática por evento;
  - presença/assinatura simples.
- **Aceite**: 100% das regras críticas reproduzidas.
- **Testes**: concorrência (race condition), integração e contrato.
- **Observabilidade**: métricas de retiradas, duplicidade bloqueada, falha de assinatura.
- **Entregáveis**: API de entregas homologada.
- **Risco**: inconsistência concorrente → transação + índices únicos + retry controlado.

## Sprint 7 — Exportações PDF/Excel/CSV

- **Objetivo**: paridade de relatórios e listas.
- **Backlog**:
  - reimplementar exportadores;
  - templates PDF fiéis ao modelo;
  - testes snapshot de layout.
- **Aceite**: aprovação visual/funcional com usuários-chave.
- **Testes**: golden files PDF/Excel/CSV.
- **Observabilidade**: taxa de falha de exportação e tempo de geração.
- **Entregáveis**: módulo de export completo.
- **Risco**: fidelidade visual → validação com checklist pixel/estrutura.

## Sprint 8 — Equipamentos + empréstimos

- **Objetivo**: controle patrimonial completo.
- **Backlog**:
  - CRUD equipamentos;
  - empréstimo/devolução/prazos;
  - histórico auditável.
- **Aceite**: estado do equipamento consistente em todos os cenários.
- **Testes**: integração com cenários de atraso/devolução.
- **Observabilidade**: alertas de empréstimo vencido.
- **Entregáveis**: API de equipamentos.
- **Risco**: transições inválidas de status → máquina de estados explícita.

## Sprint 9 — Relatórios gerenciais + elegibilidade/alertas + configurações

- **Objetivo**: inteligência operacional e parametrização.
- **Backlog**:
  - relatórios consolidados;
  - engine de elegibilidade parametrizável;
  - telas/API de configuração.
- **Aceite**: resultados equivalentes ao Python com base de referência.
- **Testes**: regressão estatística (comparação de outputs).
- **Observabilidade**: painéis de indicadores e alertas de anomalia.
- **Entregáveis**: dashboard gerencial + tuning de regras.
- **Risco**: divergência de cálculo → teste A/B com execução paralela Python x PHP.

## Sprint 10 — Hardening, migração de dados, rollout/rollback

- **Objetivo**: produção segura e reversível.
- **Backlog**:
  - hardening segurança/performance;
  - migração de dados final;
  - plano de cutover gradual;
  - rollback testado;
  - runbook operacional.
- **Aceite**: Go/No-Go com checklist completo aprovado.
- **Testes**: carga, segurança (SAST/DAST), DR drill.
- **Observabilidade**: SLOs + alertas de erro, latência, DB e jobs.
- **Entregáveis**: produção habilitada + relatório final.
- **Risco**: indisponibilidade no cutover → blue/green + feature flag + rollback em minutos.

---

## 7) Observabilidade (padrão obrigatório em todas as sprints)

## 7.1 Padrão mínimo

- Logs JSON estruturados com:
  - `timestamp`, `level`, `request_id`, `user_id`, `module`, `action`, `status_code`, `duration_ms`.
- Métricas:
  - latência HTTP (p50/p95/p99),
  - taxa de erro 4xx/5xx,
  - tempo de query DB,
  - throughput por endpoint,
  - sucesso/falha de exportações.
- Tracing:
  - plano com OpenTelemetry desde sprint 2,
  - spans por request e query crítica.
- Auditoria:
  - eventos sensíveis (CRUD, permissões, retiradas, consentimento) com trilha imutável.

## 7.2 Dashboards e alertas

- **Dashboard API**: RPS, p95, 5xx, top endpoints lentos.
- **Dashboard DB**: conexões, lock waits, queries lentas.
- **Dashboard Negócio**: retiradas/dia, bloqueios por duplicidade, elegíveis x atendidos.
- **Alertas**:
  - 5xx > limiar por 5 min,
  - p95 > 800ms por 10 min,
  - falha de exportação > 2%,
  - falha de migração de dados > 0,
  - aumento abrupto de lockout de login.

---

## 8) Checklist de produção + rollout/rollback

## Pré-produção

- [ ] Revisão de segurança (OWASP ASVS mínimo).
- [ ] Revisão LGPD (consentimento, retenção, anonimização de logs sensíveis).
- [ ] Testes de carga e capacidade.
- [ ] Backup full validado + teste de restore.
- [ ] Ensaios de migração de dados em staging com volume realístico.
- [ ] Validar contratos React com testes automatizados.

## Rollout

- [ ] Estratégia blue/green ou canary.
- [ ] Feature flags para módulos críticos.
- [ ] Janela de corte com freeze transacional.
- [ ] Monitoramento em war room nas primeiras 24–72h.

## Rollback

- [ ] Critérios objetivos de abortar cutover.
- [ ] Script de rollback de app (versão anterior).
- [ ] Estratégia de rollback de dados (snapshot + replay controlado).
- [ ] Comunicação de incidente e plano de continuidade.

---

## 9) Template de relatório por sprint (modelo pronto)

## Relatório Sprint {N}

- **Período**: {data_início} a {data_fim}
- **Objetivo da sprint**: {texto}

### 1. Sumário

{resumo executivo da sprint}

### 2. O que foi entregue

- {item 1}
- {item 2}

### 3. Evidências (prints/links/arquivos)

- PRs: {links}
- Pipelines CI: {links}
- Documentos: {links}
- Evidências visuais/exportações: {links}

### 4. Testes executados e resultados

- Unitários: {x} passando / {y} falhando
- Integração: {x} passando / {y} falhando
- Contrato: {x} passando / {y} falhando
- Segurança/performance: {resumo}

### 5. Métricas observadas

- p95 latência: {valor}
- erro 5xx: {valor}
- tempo médio de query crítica: {valor}
- taxa falha export: {valor}

### 6. Pendências e próximos passos

- {pendência 1}
- {pendência 2}

### 7. Riscos abertos

- Risco: {descrição}
  - Impacto: {baixo/médio/alto}
  - Mitigação: {ação}
  - Dono: {responsável}

---

## 10) Apêndice: inventários

## 10.1 Entidades principais identificadas

- Auth: `User`, `Role`, `user_roles`, `LoginAttempt`, `RateLimitEvent`, `PasswordResetToken`.
- Núcleo social: `Family`, `Dependent`, `Child`, `FamilyWorker`, `FoodBasket`, `VisitRequest`, `VisitExecution`.
- Entregas: `DeliveryEvent`, `DeliveryInvite`, `DeliveryWithdrawal`, `AuditLog`.
- Equipamentos: `Equipment`, `Loan`.
- Rua: `StreetPerson`, `StreetService`, `Referral`.
- Governança: `ConsentTerm`, `SystemSettings`, `MonthlyClosure`.

## 10.2 Jobs/processos especiais

- Não foram encontrados workers assíncronos explícitos (Celery/RQ/etc.) no backend atual.
- Processos pesados (exportações/PDF) rodam de forma síncrona via request.

## 10.3 Inventário de exportações

- Relatórios CSV/XLSX por módulo (`/relatorios/export.csv`, `/relatorios/export.xlsx`).
- PDFs por relatórios temáticos (`/relatorios/*.pdf`).
- PDFs de famílias/pessoas/eventos/fechamento.
- Exportações de lista de crianças por evento (XLSX/PDF).

## 10.4 Comandos de auditoria executados

- `rg --files -g 'AGENTS.md'`
- `rg -n "@(app|router)\.(get|post|put|delete|patch)" app`
- `rg -n "cpf|duplic|senha|presen|assin|consent|eligib|alert|month|mensal|retirada" app`
- inspeção manual de: `app/main.py`, `app/deliveries/routes.py`, `app/reports/routes.py`, `app/closures/routes.py`, `app/models/*.py`, `app/core/*.py`, `app/services/audit.py`, `app/eligibility/engine.py`, `app/reports/exporters.py`, `app/pdf/report_engine.py`, `pyproject.toml`, `requirements.txt`, `alembic/versions/*`.
