# Sprint 10 — Análise Pré-Implementação

Data: 2026-02-18
Contexto: Auditoria final + homologação institucional (Go-Live)

## 1) Baseline pós-sprints (confirmação)

- ✅ PDF Engine universal ativo e utilizado nos relatórios institucionais e operacionais.
- ✅ Fechamento mensal com lock retroativo ativo.
- ✅ Relatório oficial mensal com hash SHA256 e imutabilidade implementados.
- ✅ Histórico mensal com comparação e gráficos disponível.
- ✅ RBAC com papéis `Admin`, `Operador`, `Leitura` implementado (mapeável para Voluntário/Admin/Pastoral).
- ✅ LGPD com consentimento versionado e trilha de auditoria (`audit_logs`).

## 2) Divergências de escopo e riscos para homologação

### 2.1 Frontend SSR vs React
- **Situação atual:** frontend em SSR (FastAPI + Jinja2), sem SPA React.
- **Decisão institucional proposta:** manter SSR no go-live atual por estabilidade e cobertura funcional.
- **Backlog futuro (não bloqueante):** plano de migração gradual para React, caso a instituição exija padronização SPA.

### 2.2 Riscos para homologação
1. **Drift de migração detectado em `alembic check` (SQLite)**
   - Indício: comparação autogerada sinaliza FKs em `monthly_closures`.
   - Risco: divergência entre metadata e estado esperado em validações estritas de migração.
2. **PostgreSQL local indisponível no ambiente de auditoria automatizada**
   - Risco: não comprovar execução end-to-end local com Postgres nesta execução.
3. **Papel Pastoral dedicado não identificado como role própria**
   - Situação: mapeamento operacional para `Leitura` (com possíveis permissões adicionais).
   - Risco: necessidade de papel dedicado em auditorias futuras de segregação fina.

## 3) Plano de mitigação

1. **Migrações**
   - Abrir backlog técnico para reconciliar FKs reportadas no `alembic check`.
   - Rodar validação adicional em staging PostgreSQL gerenciado.
2. **Ambiente PostgreSQL**
   - Provisionar banco de homologação institucional persistente.
   - Executar `alembic upgrade head` + smoke tests de rotas críticas.
3. **RBAC Pastoral**
   - Formalizar matriz de permissões do perfil Pastoral.
   - Criar role dedicada em sprint de governança, sem bloquear go-live atual.

## 4) Critérios de aprovação da homologação (gate)

- Suíte automatizada 100% verde (`pytest` e cobertura com `pytest --cov`).
- Fluxos obrigatórios por perfil (Voluntário/Admin/Pastoral) validados e documentados.
- Evidências de geração de PDFs institucionais e oficiais com hash SHA256.
- Evidências de lock mensal e histórico imutável.
- Evidências de consentimento obrigatório e audit trail para operações críticas.
- Registro explícito de riscos remanescentes e aceite institucional formal.
