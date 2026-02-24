# FLUXO OPERACIONAL

## Fluxo macro

1. Login
2. Cadastro/atualização da família
3. Gestão de dependentes e crianças
4. Registro de atendimento social (visitas/encaminhamentos)
5. Operação de entregas por evento
6. Gestão de equipamentos e empréstimos
7. Geração de relatórios
8. Fechamento mensal
9. Emissão do relatório oficial com hash
10. Consulta de histórico e gráficos

## Regras críticas

- Não registrar entregas em mês fechado.
- Relatório oficial só após fechamento em `CLOSED`.
- Regeração de oficial apenas com `ADMIN_OVERRIDE=true`.
