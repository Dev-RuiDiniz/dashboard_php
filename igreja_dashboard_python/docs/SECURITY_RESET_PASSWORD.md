# Segurança — Reset de senha

## Fluxo
- `GET /password/forgot`: formulário para solicitar redefinição.
- `POST /password/forgot`: resposta genérica (anti-enumeração), geração de token aleatório forte e persistência apenas do hash SHA-256 em `auth.password_reset_tokens`.
- `GET /password/reset?token=...`: valida token não expirado e não utilizado.
- `POST /password/reset`: aplica política de senha existente (`MIN_PASSWORD_LENGTH` + regras de letra/número), marca `used_at` e altera senha.

## Modo dev
- Em ambiente não-produtivo, o link de reset é exibido na tela após solicitação.

## Configuração
- `PASSWORD_RESET_TOKEN_TTL_MINUTES` (default: 30).

## Limitação conhecida
- O sistema ainda não mantém trilha de sessões por usuário para invalidação seletiva imediata de sessões já emitidas.
