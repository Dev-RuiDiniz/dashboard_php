# SPRINT 3 — Análise pré-implementação (LGPD + Auditoria)

## 1) O que já existe no repositório

### Estrutura de auditoria (`audit_logs`)
- Já existe tabela/modelo `audit_logs` no domínio, criada na migration `0009_delivery_events` e mapeada em `src/app/models/delivery.py`.
- Estrutura atual é mínima: `id`, `user_id`, `action`, `entity`, `entity_id`, `created_at`.
- Não há `before_json`/`after_json` persistidos hoje.

### Logging estruturado com `user_id`
- Existe logging JSON em `src/app/core/logging.py` (`JsonFormatter`) com suporte explícito a `user_id` em `extra`.
- Middleware HTTP (`auth_middleware` em `src/app/main.py`) já popula `request.state.user` e loga cada request com `user_id`, `request_id`, método, path, status e duração.

### Padrão de timestamps nas entidades
- Predomina `created_at` com `server_default=func.now()` em entidades de domínio.
- Não há padrão consolidado de `updated_at` nas entidades principais.

### Como estão modeladas as áreas solicitadas
- **Family**: `src/app/models/family.py` com dados cadastrais, endereço, vulnerabilidade, relações (dependentes, cestas, visitas, empréstimos, crianças).
- **StreetPerson**: `src/app/models/street.py` com identificação, localização de referência, histórico de serviços e encaminhamentos.
- **Social/Ficha Social**: não há entidade chamada `SocialRecord`; o equivalente de acompanhamento social atual está em `VisitRequest`/`VisitExecution` (visitas sociais) no módulo de famílias.
- **Delivery withdrawal (Sprint 1)**: `DeliveryWithdrawal` em `src/app/models/delivery.py` e fluxos em `src/app/deliveries/routes.py`.
- **Equipment loans**: `Equipment`/`Loan` em `src/app/models/equipment.py`, rotas em `src/app/main.py` (`/equipamentos/{id}/emprestimo` e `/devolver`).

### RBAC
- RBAC via papéis/permissões em `src/app/core/auth.py` (`require_permissions`, `require_roles`) + modelos `User/Role` em `src/app/models/user.py`.
- Uso em rotas via `Depends(require_permissions(...))` ou `Depends(require_roles(...))`.

### Validações de formulário SSR
- Validação é feita na camada de rota (`src/app/main.py`) com helpers (`_require_value`, `_parse_date`, validações CPF etc.).
- Em erro, retorna `TemplateResponse(..., status_code=400)` com mensagem no formulário.

## 2) Avaliação de lacunas

### Consentimento
- Não existem campos de consentimento em `Family` ou `StreetPerson`.
- Não existe versionamento de termo de consentimento.

### Interceptação reutilizável para auditoria
- Não há middleware genérico de auditoria de operações de negócio.
- Existe uso pontual de `_create_audit_log` no módulo de entregas; pode ser evoluído para utilitário central reutilizável.

## 3) Reuso identificado

- Reusar middleware atual para obter usuário autenticado (`request.state.user`) e garantir autoria (`user_id`) nos registros.
- Reusar padrão de validação SSR já adotado (erro 400 com template) para consentimento obrigatório nos formulários.
- Reusar RBAC existente para proteger novas telas admin (`/admin/consentimento`, `/admin/audit`).

## 4) Estratégia escolhida

### Auditoria: camada de serviço/utilitário (não middleware global)
- Estratégia escolhida: **camada service/utilitária** (`log_action(...)`) chamada explicitamente nas operações críticas.
- Justificativa:
  - Permite controlar com precisão **o que** registrar (ação, entidade, before/after).
  - Facilita sanitização de dados sensíveis por tipo de operação.
  - Evita complexidade e ruído de tentar inferir alterações de domínio em middleware HTTP genérico.

### Versionamento de termo
- Criar tabela `consent_terms` com `version`, `content`, `active`, `created_at`.
- Garantir apenas 1 termo ativo por regra de aplicação (desativando os demais ao ativar novo termo).
- Novos cadastros utilizarão sempre a versão ativa.
- Criar tela/admin simples para gestão de termos.

## 5) Plano técnico para implementação

1. Migration Alembic para:
   - adicionar campos LGPD em `families`, `street_people` e `visit_requests` (preparo futuro de ficha social),
   - criar `consent_terms`,
   - evoluir `audit_logs` com `before_json`/`after_json` + índices solicitados.
2. Atualizar modelos SQLAlchemy correspondentes.
3. Implementar utilitário de auditoria central com sanitização (máscara CPF, remoção de senha/token).
4. Aplicar consentimento obrigatório nas rotas de criação (`/familias/nova`, `/rua/nova`; ficha social inexistente no momento).
5. Criar `/admin/consentimento` (Admin).
6. Criar `/admin/audit` com filtros e template.
7. Cobrir com testes pytest obrigatórios do escopo.
8. Atualizar README com seção LGPD e consulta/versionamento.
