# RELATÓRIO DE AUDITORIA DE ESCOPO

## Sistema Web de Gestão da Ação Social — Primeira Igreja Batista de Taubaté

Data da auditoria: 2026-02-18

---

## 1) Resumo executivo

### Conclusão geral
O repositório **não está aderente ao escopo consolidado completo** (Login → Dashboard → Famílias | Pessoas | Crianças | Entregas | Equipamentos | Relatórios | Usuários/Config) em sua totalidade. O sistema atual é funcional para um **subconjunto importante do domínio**: autenticação com RBAC, famílias/dependentes, cestas mensais por família, equipamentos/empréstimos, pessoas em situação de rua, visitas sociais, dashboard operacional e relatórios CSV/XLSX.

Há, porém, gaps estruturais relevantes para o escopo-alvo: ausência de módulo dedicado de crianças e eventos, ausência de fluxo de "entrega por evento" com senha/convites/presença/assinatura, ausência de PDF, ausência de recuperação de senha e ausência de trilha de auditoria persistente em banco.

### Aderência por macro-área
- **Bem coberto (MVP parcial):** Auth + RBAC, Famílias, Equipamentos, Dashboard, Relatórios básicos, migrações e testes automatizados.
- **Parcial:** Entregas (hoje tratadas como cestas por família/mês, sem eventos), LGPD/segurança (há base técnica e documentação, mas faltam controles de produto), Configurações administrativas.
- **Ausente:** Crianças/eventos infantis dedicados, lista automática de crianças por evento, exportação PDF, engine formal de elegibilidade configurável, consentimento digital e assinatura.

### Recomendação executiva
Priorizar um plano P0 para fechar os gaps de negócio crítico (módulo de entregas por evento, crianças, consentimento LGPD e trilha auditável), mantendo a base atual como fundação.

---

## 2) Stack e arquitetura encontrada

## 2.1 Stack real identificada
- **Backend web:** FastAPI.
- **Frontend:** SSR com Jinja2 (não há React/Vite).
- **Banco:** SQLAlchemy 2 + Alembic; SQLite default e PostgreSQL em produção.
- **Auth:** JWT em cookie HTTPOnly.
- **Autorização:** RBAC por permissões (Admin/Operador/Leitura).
- **Deploy:** Docker Compose (web + postgres) e adapter para Vercel (`api/index.py` + `vercel.json`).

## 2.2 Estrutura principal do repositório
- `src/app/main.py` (rotas web e fluxos).
- `src/app/models/` (entidades SQLAlchemy).
- `src/app/dashboard/` (queries e página dashboard).
- `src/app/reports/` (queries, exports e tela de relatórios).
- `alembic/versions/` (migrações).
- `templates/` (telas SSR).
- `tests/` (testes de auth, família, equipamentos, dashboard/relatórios, rua, reset, backup).

## 2.3 Como rodar e variáveis
- Execução local: `uvicorn app.main:app --reload --app-dir src`.
- Migrações: `alembic upgrade head`.
- Deploy Docker: `docker compose up -d --build`.
- Variáveis principais: `DATABASE_URL`, `SECRET_KEY`, `APP_ENV`, `COOKIE_SECURE`, `DEFAULT_ADMIN_*`, `MIN_PASSWORD_LENGTH`.

## 2.4 CI/CD
- Não foi encontrado workflow de GitHub Actions no repositório.
- Há configuração de rota para Vercel e suporte a Docker Compose.

---

## 3) Diagrama textual da arquitetura

```text
Browser (Jinja SSR + Bootstrap)
  -> FastAPI (src/app/main.py + routers /dashboard e /relatorios)
    -> SQLAlchemy Session
      -> SQLite (dev default) ou PostgreSQL (prod)
```

### Autenticação/autorização
- Middleware lê token Bearer/cookie, decodifica JWT e popula `request.state.user`.
- Guardas por permissão em rotas (`require_permissions`).
- Papéis atuais: Admin, Operador, Leitura.

---

## 4) Mapa de rotas (Frontend/Backend)

> Observação: a aplicação é SSR; portanto as “rotas frontend” correspondem às rotas HTTP renderizadas no backend.

## 4.1 Principais rotas backend/web
- Públicas: `/`, `/health`, `/login`, `POST /login`, `/logout`, `/api/cep/{cep}`.
- Dashboard: `/dashboard`, `/dashboard/mapa-calor-bairros`.
- Usuários: `/admin/users`, `/admin/users/new`, `/admin/users/{id}/edit`.
- Famílias: `/familias`, `/familias/nova`, `/familias/{id}`, edição/inativação.
- Dependentes: criação/edição/remoção sob `/familias/{id}/dependentes/*`.
- Cestas: `POST /familias/{id}/cestas` + editar/remover.
- Visitas sociais: `POST /familias/{id}/visitas` e execução.
- Equipamentos: listagem, cadastro, edição, empréstimo, devolução.
- Rua: `/rua`, `/rua/nova`, `/rua/{id}`, atendimentos, encaminhamentos.
- Relatórios: `/relatorios`, `/relatorios/export.csv`, `/relatorios/export.xlsx`.

---

## 5) Mapa de entidades do banco

## 5.1 Entidades implementadas
- **Auth:** `users`, `roles`, `user_roles`.
- **Domínio:** `families`, `dependents`, `food_baskets`, `equipment`, `loans`, `street_people`, `street_services`, `referrals`, `visit_requests`, `visit_executions`.

## 5.2 Entidades esperadas no escopo consolidado e status
- `users` ✅
- `families` ✅
- `family_members` 🟡 (representado por `dependents`, sem separação completa por papel de membro)
- `children` ❌ (não há tabela dedicada)
- `social_records` ❌ (não há ficha social estruturada dedicada)
- `deliveries`/`delivery_events` 🟡 (há `food_baskets` mensal por família, sem eventos)
- `equipment` ✅
- `equipment_loans` ✅ (`loans`)
- `referrals` ✅ (no domínio de rua)
- `spiritual_followups` ❌
- `reports` 🟡 (geração dinâmica sem persistência de relatório)
- `audit_logs` ❌ (sem tabela dedicada de auditoria)

---

## 6) Matriz Escopo x Status

| Módulo | Subitem | Status | Evidência | Falta/Observação |
|---|---|---|---|---|
| A) Auth/Perfis | Login JWT | ✅ | `POST /login`, middleware JWT/cookie | — |
| A) Auth/Perfis | Perfis Voluntário/Admin/Pastoral | 🟡 | Papéis: Admin/Operador/Leitura | Não existem perfis “Voluntário/Pastoral” nomeados |
| A) Auth/Perfis | Recuperação de senha | ✅ | Rotas SSR de forgot/reset com token único e expiração | Implementado no Sprint 4 |
| A) Auth/Perfis | Bloqueio por tentativas | ✅ | Lockout por tentativas + rate limit em /login | Implementado no Sprint 4 |
| A) Auth/Perfis | Auditoria de acesso | 🟡 | Logs estruturados request/auth | Falta persistir audit trail em DB |
| B) Ficha Social Pessoa/Atendimento | Cadastro social completo (campos do escopo) | ❌ | Não há entidade/tela de ficha social dedicada | Criar módulo social_records |
| B) Ficha Social Pessoa/Atendimento | CPF + bloqueio duplicado | ✅ | `_validate_cpf`, `_cpf_conflict`, `_validate_street_cpf` | — |
| B) Ficha Social Pessoa/Atendimento | Consentimento + assinatura + timestamp | ❌ | Sem campos/telas para consentimento assinado | Implementar coleta e persistência |
| B) Ficha Social Pessoa/Atendimento | Timeline de atendimentos | 🟡 | Há histórico em rua e visitas sociais | Não há timeline unificada por pessoa/família |
| B) Ficha Social Pessoa/Atendimento | Anotações restritas pastoral/admin | ❌ | Sem perfil pastoral + campo restrito | Implementar RBAC por nota sensível |
| C) Famílias | Cadastro responsável CPF único | ✅ | `families.responsible_cpf unique`; validação app | — |
| C) Famílias | Endereço com CEP automático | ✅ | `/api/cep/{cep}` + JS em `family_form.html` | — |
| C) Famílias | Wizard + abas detalhadas | ✅ | Rotas SSR por etapas e organização em abas na ficha | Implementado no Sprint 4 |
| C) Famílias | Socioeconômico + pendências | 🟡 | Campos `socioeconomic_profile` e `documentation_status` | Sem motor de pendências formal |
| C) Famílias | Membros adultos/crianças vinculados | 🟡 | `dependents` vinculados à família | Sem distinção robusta adulto/criança e sem módulo children |
| C) Famílias | Ações rápidas (entrega, empréstimo, PDF) | ✅ | Histórico no detalhe + endpoint `/familias/{id}/export.pdf` | Implementado no Sprint 4 |
| D) Crianças | Módulo dedicado + vínculo família | ✅ | Tabela `children`, rotas SSR e templates dedicados implementados | CRUD completo com RBAC e vínculo familiar ativo |
| D) Crianças | Import/associação | 🟡 | Associação manual via `family_id` no CRUD de crianças | Importação em lote ainda pendente |
| D) Crianças | Exportação por evento | ✅ | Exportações em `/entregas/eventos/{id}/criancas/export.xlsx` e `/export.pdf` | Baseada em famílias confirmadas (`WITHDRAWN`) |
| E) Entregas Cesta | Criar/abrir/encerrar eventos | ❌ | Sem entidade “evento de entrega” | Implementar delivery_events |
| E) Entregas Cesta | Seleção convidados (manual/critério) | ❌ | Sem lista de convidados por evento | Implementar |
| E) Entregas Cesta | Senha automática | ❌ | Sem campo/regra de senha | Implementar |
| E) Entregas Cesta | Bloqueio duplicidade no mês | ✅ | `uq_food_basket_family_month` + validação app/teste | Regra existe no modelo atual (não por evento) |
| E) Entregas Cesta | Presença/retirada + assinatura | ❌ | Sem campos/fluxo de retirada assinada | Implementar |
| E) Entregas Cesta | Responsável pela entrega | ❌ | Não há `delivered_by_user_id` em cesta | Implementar rastreabilidade |
| E) Entregas Cesta | Export PDF/Excel/CSV + impressão | 🟡 | CSV/XLSX em relatórios | Falta PDF e modelo de impressão específico |
| F) Lista automática crianças por evento | Filtro famílias confirmadas | ✅ | Lista em `/entregas/eventos/{id}/criancas` com convites `WITHDRAWN` | Query com join Family+Child sem N+1 |
| F) Lista automática crianças por evento | Export PDF/Excel | ✅ | Endpoints dedicados para XLSX e PDF | Pronto para impressão A4 |
| G) Equipamentos | Cadastro com código automático | ✅ | `_generate_equipment_code` (BEN-XX) | — |
| G) Equipamentos | Status disponível/emprestado/manutenção | ✅ | `EquipmentStatus` | — |
| G) Equipamentos | Empréstimo/devolução com prazo | ✅ | Rotas de empréstimo/devolução + due_date | — |
| G) Equipamentos | Termo de empréstimo | ❌ | Sem upload/termo aceito | Implementar |
| G) Equipamentos | Histórico por família | ✅ | Relação `Family.loans` e tela detalhe família | — |
| G) Equipamentos | Pendências de devolução | 🟡 | Dashboard mostra atrasos | Falta relatório dedicado de pendências/ações |
| H) Dashboard operacional | Cards e métricas | ✅ | KPIs de famílias, cestas, equipamentos, visitas, alertas | — |
| H) Dashboard operacional | Alertas docs/visita/sem atualização | 🟡 | Alertas de cesta/vulnerabilidade/atraso/visitas | Falta alerta explícito de documentação |
| H) Dashboard operacional | Próximos eventos/últimos atendimentos | 🟡 | Visitas e atendimentos aparecem parcialmente | Sem agenda de eventos de entrega |
| H) Dashboard operacional | Busca global | ❌ | Não há endpoint de busca global | Implementar |
| H) Dashboard operacional | Filtros bairro/status/CPF/necessidade | 🟡 | Filtros em famílias + mapa por bairro | Falta filtro unificado global por necessidade |
| I) Relatórios gerenciais | Filtros mês/ano | ✅ | Query params `year/month` | — |
| I) Relatórios gerenciais | Cobrir relatórios do escopo completo | 🟡 | famílias/cestas/equipamentos/visitas/rua/bairros/alertas + lista de crianças por evento | Ainda faltam elegibilidade/espiritual |
| I) Relatórios gerenciais | Export PDF/Excel/CSV | ✅ | CSV/XLSX globais e PDF/XLSX para lista de crianças por evento | Cobertura PDF inicial entregue no módulo de crianças |
| J) Usuários/Config | CRUD de usuários/perfis | ✅ | Listar/criar/editar usuários + roles | — |
| J) Usuários/Config | Categorias encaminhamento | ❌ | Encaminhamento de rua usa campos simples | Falta cadastro parametrizável |
| J) Usuários/Config | Texto padrão consentimento | ❌ | Sem configuração de termo | Implementar |
| J) Usuários/Config | Parâmetros elegibilidade | ❌ | Sem tela/config de regras | Implementar |
| J) Usuários/Config | Limite entregas/mês | ❌ | Sem parâmetro configurável | Regra é fixa por unique mensal/família |
| J) Usuários/Config | Backup status | 🟡 | Há scripts/CLI backup/restore | Sem tela/status admin |
| K) Segurança/LGPD | Senha com hash forte | ✅ | `passlib`/`bcrypt` | — |
| K) Segurança/LGPD | Controle por função | ✅ | Guardas RBAC por permissão | — |
| K) Segurança/LGPD | Logs de auditoria (quem fez o quê) | 🟡 | Logs HTTP com `user_id` | Sem trilha persistente por operação de negócio |
| K) Segurança/LGPD | Consentimento digital armazenado | ❌ | Ausente em modelo/tela | Implementar |
| K) Segurança/LGPD | Backup automático/estratégia | 🟡 | Estratégia documentada + scripts | Automatização depende de operação externa |
| K) Segurança/LGPD | Proteção de dados sensíveis em logs | 🟡 | Dashboard mascara CPF/RG em tabela | Não há garantia global de mascaramento em todos logs |
| L) Elegibilidade automática | Sugerir famílias aptas | 🟡 | Alertas por vulnerabilidade e intervalo de cestas | Não há engine explícita de sugestão |
| L) Elegibilidade automática | Alertar documentação pendente | ✅ | Engine com parâmetro `require_documentation_complete` + filtro em dashboard | — |
| L) Elegibilidade automática | Sem atualização há X meses | 🟡 | Há regra de meses sem cesta | Falta critério configurável por atualização cadastral |
| L) Elegibilidade automática | Marcar necessidade de visita | 🟡 | Módulo de visitas existe | Falta regra automática de necessidade |
| L) Elegibilidade automática | Engine/config + UI | ✅ | `system_settings`, tela `/admin/config` e seção de famílias elegíveis no dashboard | — |

---

## 7) Gaps detalhados (com evidências)

## 7.1 Entregas por evento não implementadas
Hoje “entrega” é `food_baskets` por família/período, com unicidade mensal por família. Não há entidade de evento, convidado, presença, senha ou retirada assinada.

**Evidências:**
- Modelo `FoodBasket` possui `family_id`, `reference_year`, `reference_month`, `status`, `notes`.
- Rotas de cesta só criam/alteram/removem registros por família (`/familias/{id}/cestas`).

## 7.2 Crianças/eventos infantis ausentes
Não há tabela ou rotas específicas de crianças; `dependents` é genérico.

**Evidências:**
- Entidades de domínio não incluem `children`.
- Templates/rotas não apresentam módulo dedicado de crianças.

## 7.3 LGPD de consentimento digital ausente
Não há persistência de consentimento, assinatura simples ou versionamento de termo no domínio.

**Evidências:**
- Sem campos de consentimento em `families`, `dependents`, `street_people`, `food_baskets` etc.
- Sem telas de aceite/assinatura.

## 7.4 Auditoria persistente ausente
Existe logging estruturado de requests, mas sem tabela `audit_logs` para trilha de negócio (create/update/delete por recurso).

**Evidências:**
- Middleware registra logs com metadados de request.
- Não existe modelo/migration para `audit_logs`.

## 7.5 Relatórios sem PDF
A exportação contempla CSV e XLSX, mas não PDF.

**Evidências:**
- Endpoints `/relatorios/export.csv` e `/relatorios/export.xlsx`.
- Ausência de endpoint/exportador PDF.

---

## 8) Auditoria da modelagem e consistência de DB

## 8.1 Migrações e consistência
- Migrações numeradas de `0001` a `0008` com evolução incremental.
- `0008` move tabelas para schemas `auth` e `domain` em PostgreSQL.

## 8.2 Chaves/índices relevantes
- CPF responsável em família é `unique`.
- CPF em dependente e pessoa em situação de rua também possui unicidade quando preenchido.
- `FoodBasket` possui `UniqueConstraint(family_id, reference_year, reference_month)` para bloquear duplicidade mensal.
- Relacionamento `dependents.family_id`, `loans.family_id/equipment_id`, visitas etc. com FKs e índices.

## 8.3 Rastreabilidade temporal
- Entidades principais têm `created_at`.
- Algumas operações registram usuário em visitas (`requested_by_user_id`, `executed_by_user_id`).
- Não há padrão homogêneo `updated_at` em todas entidades.

---

## 9) Auditoria de qualidade: testes, lint, observabilidade

## 9.1 Testes existentes
Há suíte pytest cobrindo autenticação/RBAC, família/CPF/duplicidade de cesta, equipamentos, rua, dashboard/relatórios, reset e backup.

Coberturas relevantes já presentes:
- Duplicidade CPF: testes de família.
- Bloqueio duplicidade de cesta no mês: teste específico.
- RBAC por perfil: testes de rotas proibidas.

Lacunas de teste (porque funcionalidade ainda não existe):
- Geração de senha por evento de entrega.
- Consentimento obrigatório com assinatura/timestamp.
- Fluxo de crianças/eventos.
- Auditoria persistente.

## 9.2 Observabilidade
- Logging estruturado com `request_id`, path, duração, status e `user_id`.
- Base adequada para observabilidade operacional, mas sem persistência analítica interna.

---

## 10) Próximos passos priorizados

## P0 (MVP do escopo consolidado)
1. **Implementar módulo de Entregas por Evento** (eventos, convidados, senha, presença/retirada, responsável, bloqueio mensal por regra de negócio). **Tamanho: grande**.
2. **Implementar módulo de Crianças** (entidade, cadastro, vínculo familiar, listagem por evento, export). **Tamanho: grande**.
3. **Adicionar consentimento digital LGPD** (termo versionado, aceite assinado simples, timestamp e usuário responsável). **Tamanho: médio/grande**.
4. **Criar trilha de auditoria persistente** (`audit_logs` + interceptação de operações críticas). **Tamanho: médio**.
5. **Adicionar recuperação de senha e proteção de brute-force** (rate limit/lockout). **Tamanho: médio**.

## P1
1. **Exportação PDF** para relatórios e comprovantes de entrega. **Tamanho: médio**.
2. **Dashboard com busca global e alertas de documentação**. **Tamanho: médio**.
3. **Configurações administrativas de elegibilidade e limites mensais**. **Tamanho: médio**.

## P2
1. **Motor de elegibilidade configurável (UI + regras)** com versionamento de parâmetros. **Tamanho: grande**.
2. **Aprimorar governança LGPD operacional** (ciclo de retenção e atendimento ao titular com workflow no sistema). **Tamanho: médio**.

---

## 11) Riscos identificados

1. **LGPD:** sem consentimento digital e sem fluxo explícito de direitos do titular no produto.
2. **Segurança:** sem recuperação de senha segura e sem bloqueio por tentativas.
3. **Rastreabilidade:** sem `audit_logs` persistente por evento de negócio.
4. **Aderência funcional:** ausência de módulos de crianças e entregas por evento compromete escopo operacional principal.
5. **Dados órfãos/regra incompleta:** ausência de camadas de governança sobre atualização cadastral e elegibilidade pode gerar decisões inconsistentes.

---

## 12) Checklist DoD por módulo

## A) Autenticação e perfis
- [x] Login funcional com JWT cookie.
- [x] RBAC por permissões aplicado nas rotas.
- [x] Recuperação de senha.
- [x] Bloqueio por tentativas / rate limiting.
- [ ] Auditoria persistente de login/logout e falhas.

## B) Ficha social
- [ ] Entidade `social_records` com campos obrigatórios do escopo.
- [ ] Consentimento obrigatório com assinatura e timestamp.
- [ ] Timeline unificada de atendimentos por pessoa/família.
- [ ] Notas restritas por perfil pastoral/admin.

## C) Famílias
- [x] CRUD principal e CPF único com validação.
- [x] CEP automático.
- [x] Dependentes vinculados.
- [x] Histórico de cestas/visitas/empréstimos no detalhe.
- [x] Wizard por etapas + abas.
- [x] Geração PDF simples da ficha.

## D) Crianças
- [x] Entidade e CRUD dedicados.
- [x] Vínculo familiar e associação manual (`family_id`).
- [x] Export por evento (XLSX/PDF).

## E) Entregas
- [ ] Entidade de evento de entrega.
- [ ] Lista de convidados manual/automática.
- [ ] Senha automática de retirada.
- [x] Regra anti-duplicidade mensal (no modelo atual de cesta/família).
- [ ] Presença/retirada/assinatura/responsável.
- [ ] PDF/Excel/CSV no formato de evento + impressão.

## F) Lista automática de crianças por evento
- [x] Geração da lista por evento.
- [x] Export PDF/Excel.

## G) Equipamentos
- [x] Cadastro e código automático.
- [x] Empréstimo/devolução com prazo.
- [x] Histórico por família.
- [ ] Termo de empréstimo assinado.
- [ ] Relatório dedicado de pendências operacionais.

## H) Dashboard
- [x] Cards e métricas principais.
- [x] Alertas de cesta/vulnerabilidade/empréstimo/visitas.
- [ ] Busca global.
- [x] Alertas de documentação pendente do escopo.

## I) Relatórios
- [x] Filtros mês/ano.
- [x] Export CSV e XLSX.
- [ ] Export PDF.
- [ ] Cobertura de relatórios de crianças/eventos/elegibilidade/espiritual.

## J) Usuários/Config
- [x] CRUD de usuários e perfis.
- [ ] Configurações de elegibilidade e limite mensal.
- [ ] Catálogo de categorias e textos padrão de consentimento.
- [ ] Status operacional de backup via interface.

## K) Segurança/LGPD
- [x] Hash de senha + RBAC.
- [x] Logs estruturados de request.
- [ ] Consentimento digital armazenado.
- [ ] Auditoria persistente de ações de negócio.
- [ ] Política técnica de proteção de PII em logs em toda a aplicação.

## L) Elegibilidade automática
- [x] Sinais de alerta parcial (sem cesta, vulnerabilidade).
- [ ] Motor configurável completo com UI administrativa.
- [ ] Alertas de documentação e atualização cadastral parametrizados.

---

## 13) Como validar os principais itens (manual/automatizado)

1. **RBAC**
   - Login com usuário Leitura e tentar acessar `/equipamentos/novo` → esperado 403.
2. **Duplicidade CPF família**
   - Criar duas famílias com mesmo CPF → esperado erro 400 na segunda.
3. **Duplicidade de cesta no mês**
   - Registrar 2 cestas `MM/AAAA` para mesma família → esperado bloqueio na segunda.
4. **Exportações**
   - Acessar `/relatorios/export.csv` e `/relatorios/export.xlsx` com usuário de gestão.
5. **Ausências de escopo**
   - Tentar localizar rotas/modelos de `children`, `delivery_events`, `audit_logs`, recuperação de senha, consentimento assinado → inexistentes.


---

## Atualização SPRINT 1 — Entregas por Evento (implementado)

### Novos artefatos

- Migração `0009_delivery_events` com:
  - `delivery_events`
  - `delivery_invites`
  - `delivery_withdrawals`
  - `audit_logs`
- Novas rotas API:
  - `POST /entregas/eventos`
  - `POST /entregas/eventos/{id}/convidar`
  - `POST /entregas/eventos/{id}/retirada/{family_id}`
  - `GET /entregas/eventos/{id}/export.csv`
  - `GET /entregas/eventos/{id}/export.xlsx`

### Compatibilidade com legado

- `food_baskets` preservado para histórico.
- Camada de transição com flag `FEATURE_EVENT_DELIVERY` para descontinuar criação legada quando necessário.
- Sem remoção de funcionalidades existentes.

### Auditoria persistente

- Ações críticas de evento registradas em `audit_logs`.


- [x] Export PDF (evento, ficha família, lista crianças).
