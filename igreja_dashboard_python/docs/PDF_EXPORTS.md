# Exportações PDF

## Stack

- Motor central institucional: `generate_report_pdf` em `src/app/pdf/report_engine.py`.
- Sem dependências de sistema externo para PDF (renderização via bytes PDF nativo da aplicação).

## Endpoints

### Relatórios agregados

- `GET /relatorios/familias.pdf`
- `GET /relatorios/cestas.pdf`
- `GET /relatorios/criancas.pdf`
- `GET /relatorios/encaminhamentos.pdf`
- `GET /relatorios/equipamentos.pdf`
- `GET /relatorios/pendencias.pdf`

### Exportações operacionais

- `GET /entregas/eventos/{id}/export.pdf`
- `GET /entregas/eventos/{id}/criancas/export.pdf`
- `GET /familias/{id}/export.pdf`
- `GET /pessoas/{id}/export.pdf`

## RBAC

As rotas PDF respeitam as mesmas permissões de leitura dos módulos relacionados.
