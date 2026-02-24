# Segurança e RBAC

## Objetivo

Definir de forma explícita as regras de autorização por papel para fechamento da Fase 5A.

## Matriz de permissões

| Papel | manage_users | view_users | manage_families | view_families | manage_equipment | view_equipment | manage_baskets | view_baskets | manage_street | view_street | manage_visits | view_visits |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Admin | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Operador | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Leitura | ❌ | ❌ | ❌ | ✅ | ❌ | ✅ | ❌ | ✅ | ❌ | ✅ | ❌ | ✅ |

## Regras de guardas

- `view_*` permite acesso a listagens e painéis de consulta.
- `manage_*` permite operações de escrita (criar/editar/remover).
- Gestão de usuários:
  - Listagem (`/admin/users`) usa `view_users`.
  - Criação/edição de usuários usa `manage_users`.
- Relatórios:
  - Visualização da página (`/relatorios`) usa permissões de visualização.
  - Exportações (`/relatorios/export.csv` e `/relatorios/export.xlsx`) usam permissões de gestão.

## Cobertura de testes (negativos)

Os testes automatizados validam negação de acesso para cenários críticos:

- Operador não pode acessar rotas de administração de usuários.
- Leitura não pode acessar gestão de usuários.
- Leitura não pode acessar criação de equipamentos.
- Leitura não pode exportar relatórios CSV.

- Domínio de rua (`/rua`) usa `view_street` para consulta e `manage_street` para cadastros/atualizações.
