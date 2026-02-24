# FLUXO_VALIDADO_TELAS

## Evidências de validação (SSR FastAPI/Jinja)

1. **Navegação principal validada**: `/dashboard`, `/familias`, `/pessoas`, `/criancas`, `/entregas`, `/equipamentos`, `/relatorios`, `/admin/usuarios`, `/admin/config`.
2. **Fluxo de autenticação validado**: login web (`/login`) e API (`/auth/login`) + reset de senha.
3. **Fluxo de entregas validado**: criação/listagem de eventos, convite, retirada, encerramento, exports.
4. **Fluxo de UX extra validado**: busca global e endpoint de timeline agregado.

## Divergências documentadas
- O módulo de “Pessoas/Ficha Social” está implementado no sistema sob o namespace **`/rua`**. Para compatibilidade com o fluxo oficial, foi criado alias `/pessoas`.

## Prints
- Tela de entregas SSR atualizada (lista de eventos).
