# Sprint 4 — Análise pré-implementação

## O que foi encontrado na auditoria

### Login atual
- Rotas SSR já existentes: `GET /login`, `POST /login`, `GET /logout`.
- `POST /login` busca usuário por e-mail normalizado (`func.lower(User.email)`), valida senha com `verify_password` e retorna cookie de autenticação JWT.
- O token JWT é criado por `create_access_token` (`HS256`) e persistido no cookie HTTP-only via `set_auth_cookie`.
- Middleware (`auth_middleware`) resolve usuário por cookie ou header Bearer e injeta em `request.state.user`.
- Não existe lockout nem rate limit específico de login.

### Reset de senha
- Não há rotas de reset/forgot password no app.
- O relatório de auditoria já sinaliza lacuna (`Recuperação de senha: ❌`).

### Persistência de usuários e hash
- Modelo `User` em `src/app/models/user.py` (schema `auth` em PostgreSQL) com `hashed_password`.
- Hash padrão: `passlib` com `pbkdf2_sha256`; fallback para `bcrypt` legado no `verify_password`.

### Rate limit / lockout
- Não há infra dedicada de lockout por tentativas no login.
- Não há middleware de rate limiting por IP para `/login`.

### Base de busca existente
- Famílias: filtros por nome/CPF/bairro/vulnerabilidade em `/familias`.
- Crianças: filtros por família/idade/sexo/nome em `/criancas`.
- Equipamentos: listagem sem filtro textual em `/equipamentos`.
- Entregas/eventos: consultas existentes em `deliveries/routes.py` para listagens e exportações.

### Templates SSR e UX
- Organização Jinja + Bootstrap em `templates/`.
- Layout padrão via `templates/base.html` com navbar.
- Mensagens de erro por contexto de template (campo `error`) e `alert` Bootstrap.
- Não há wizard multi-step para família; cadastro atual é formulário único (`family_form.html`).
- Tela de detalhe da família existe, porém sem abas de navegação.

### Relatórios CSV/XLSX e PDF
- Exportadores CSV/XLSX já implementados em `src/app/reports/exporters.py`.
- Já existe geração de PDF manual para lista de crianças por evento (`src/app/pdf/children.py` + rota `/entregas/eventos/{id}/criancas/export.pdf`).
- Dependências atuais não incluem WeasyPrint/ReportLab.

## Reaproveitamento planejado
- Reusar middleware/auth JWT/cookie e dependências RBAC atuais (`require_permissions`/`require_roles`).
- Reusar `validate_password` e `settings.min_password_length` para política de senha.
- Reusar padrões de templates SSR existentes (cards, alerts, forms Bootstrap).
- Reusar consultas de famílias/crianças/equipamentos/eventos para busca global.
- Reusar estrutura de exportação e módulo `src/app/pdf` para novos PDFs.

## Decisão de gerador PDF
- **Escolha: ReportLab**.
- Motivo: menor risco operacional em ambiente serverless/containers sem dependências externas de renderização HTML (em comparação com WeasyPrint).

## Estratégia de lockout + rate limit (compatível com SSR)
- Lockout por tentativas em tabela dedicada (`login_attempts`) para suporte a múltiplas instâncias.
- Regra: 5 falhas em 15 min por `identity+ip`; bloqueio por 15 min.
- Reforço por usuário (`user_id`) quando identidade corresponde a usuário existente.
- Rate limit complementar por IP em `/login` com contador em DB (tabela `rate_limit_events`) para ambiente sem estado.
- Respostas de erro de autenticação permanecerão genéricas para evitar enumeração.

## Impacto em banco e migrações
- Nova tabela `auth.password_reset_tokens`.
- Nova tabela `auth.login_attempts`.
- Nova tabela `auth.rate_limit_events`.
- Índices em colunas de busca temporal (`expires_at`, `attempted_at`, `window_start`) e relacionamento (`user_id`).
- Migração reversível com `downgrade` removendo tabelas/índices.
