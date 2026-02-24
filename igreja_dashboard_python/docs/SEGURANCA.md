# SEGURANÇA

## Controles técnicos

- RBAC com papéis `Admin`, `Operador`, `Leitura`.
- Dependências de autorização por rota (`require_roles` e `require_permissions`).
- Cookie HTTPOnly para sessão autenticada.
- Lockout e rate limit em login.
- Reset de senha com token e expiração.
- Auditoria de ações críticas.

## Boas práticas de operação

- Trocar credenciais padrão no primeiro acesso.
- Rodar em HTTPS em produção.
- Definir `SECRET_KEY` forte em ambiente produtivo.
- Monitorar eventos de lockout e tentativas de acesso indevido.
