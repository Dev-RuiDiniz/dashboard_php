# Configurações do sistema (Admin)

Tela: `/admin/config` (acesso Admin).

## Parâmetros

- `delivery_month_limit` (limite de entregas no mês)
  - `0`: desabilita limite mensal.
  - `> 0`: bloqueia elegibilidade quando a família já tem N entregas no mês atual.

- `min_months_since_last_delivery` (meses mínimos sem entrega)
  - Família só é elegível se estiver sem entrega há pelo menos X meses.

- `min_vulnerability_level` (0 a 4)
  - 0 = Sem vulnerabilidade
  - 1 = Baixa
  - 2 = Média
  - 3 = Alta
  - 4 = Extrema

- `require_documentation_complete`
  - Quando habilitado, exige documentação em estado considerado completo (`OK`, `COMPLETE`, `COMPLETO`, `COMPLETA`, `REGULAR`).

## Valores padrão

- `delivery_month_limit = 1`
- `min_months_since_last_delivery = 2`
- `min_vulnerability_level = 2`
- `require_documentation_complete = true`

## Exemplos práticos

1. Priorizar casos graves:
   - `min_vulnerability_level = 3`
   - mostra principalmente Alta/Extrema.

2. Campanha ampla emergencial:
   - `min_vulnerability_level = 1`
   - `min_months_since_last_delivery = 0`
   - `delivery_month_limit = 0`

3. Mutirão com foco em regularização documental:
   - `require_documentation_complete = true`
