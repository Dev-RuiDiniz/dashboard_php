# API Contract TBD por Tela (derivado de SCREEN_RULES)

> Este documento não define payload final; lista apenas endpoints necessários por tela até fechamento de contrato oficial.

## Autenticação
- `/login`: autenticação de sessão/token.
- `/recuperar-senha`: solicitação de recuperação e redefinição.

## Dashboard
- `/dashboard`: indicadores consolidados e alertas/chips.

## Famílias
- `/familias`: listagem paginada + filtros.
- `/familias/nova`: criação (wizard A/B/C/D).
- `/familias/{id}`: detalhe + timeline/histórico.

## Pessoas
- `/pessoas`: listagem + filtros.
- `/pessoas/novo-atendimento`: criação de atendimento com consentimento.
- `/pessoas/{id}`: detalhe + timeline de fichas/atendimentos.

## Crianças
- `/criancas`: listagem + filtros.
- `/criancas/nova`: criação.
- `/criancas/{id}/editar`: edição.

## Entregas/Eventos
- `/entregas/eventos`: listagem de eventos.
- `/entregas/eventos/novo`: criação de evento.
- `/entregas/eventos/{id}/convidados`: convidados/retirada.
- `/entregas/eventos/{id}/criancas`: crianças do evento.

## Equipamentos
- `/equipamentos`: listagem.
- `/equipamentos/novo`: criação.
- `/equipamentos/{id}`: detalhe.
- `/equipamentos/emprestimos`: empréstimos/devoluções.

## Relatórios
- `/relatorios/mensais`: listagem/exportações.

## Administração
- `/admin/usuarios`: gestão de usuários.
- `/admin/config`: gestão de configurações.
