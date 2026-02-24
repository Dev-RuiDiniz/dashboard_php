# LGPD

## Controles implementados

- Consentimento ativo gerenciável pela administração (`/admin/consentimento`).
- Registro de eventos em trilha de auditoria (`AuditLog`).
- Sanitização de payload de auditoria com mascaramento de CPF e remoção de campos sensíveis.
- Fluxo de autenticação com reset de senha e bloqueio temporário por tentativas inválidas.

## Diretrizes operacionais

1. Coletar consentimento antes do tratamento de dados pessoais.
2. Manter trilha de auditoria ativa para eventos críticos.
3. Restringir telas administrativas a perfil com `manage_users`.
4. Revisar periodicamente retenção e exportações de dados.
