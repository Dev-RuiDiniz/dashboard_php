# Segurança — Lockout e Rate Limit de login

## Lockout
- Tabela: `auth.login_attempts`.
- Regra: 5 falhas em 15 minutos por combinação `identity+ip` bloqueiam novas tentativas no período.
- Reforço por `user_id` quando identidade corresponde a usuário existente.

## Rate limit
- Tabela: `auth.rate_limit_events`.
- Regra padrão: 30 requisições em 5 minutos por IP na rota `/login`.
- Excesso retorna `HTTP 429`.

## Configuração
- `LOGIN_RATE_LIMIT_MAX_REQUESTS` (default 30)
- `LOGIN_RATE_LIMIT_WINDOW_MINUTES` (default 5)
- `LOGIN_LOCKOUT_MAX_FAILURES` (default 5)
- `LOGIN_LOCKOUT_WINDOW_MINUTES` (default 15)
