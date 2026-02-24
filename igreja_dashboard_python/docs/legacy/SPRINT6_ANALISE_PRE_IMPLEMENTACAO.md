# SPRINT 6 — Análise pré-implementação de PDF

## 1) Auditoria obrigatória

### 1.1 Onde PDFs já existem

Implementações identificadas no estado atual:

- `GET /familias/{family_id}/export.pdf` em `src/app/main.py`, usando `render_pdf(...)` com tabela simples de chave/valor.
- `GET /entregas/eventos/{event_id}/export.pdf` em `src/app/deliveries/routes.py`, também usando `render_pdf(...)`.
- `GET /entregas/eventos/{event_id}/criancas/export.pdf` em `src/app/deliveries/routes.py`, usando `build_event_children_pdf(...)`.

### 1.2 Como estão sendo gerados

Motor atual é **geração manual de bytes PDF** (sem ReportLab/WeasyPrint/HTML->PDF):

- `src/app/pdf/render.py` contém `render_pdf(...)` com objetos PDF básicos e texto posicionado linha a linha.
- `src/app/pdf/children.py` contém outro gerador semelhante para lista de crianças.
- Não há dependências PDF dedicadas em `requirements.txt`/`pyproject.toml`.

### 1.3 Duplicação de código

Há duplicação entre `render.py` e `children.py`:

- escape de texto PDF repetido;
- montagem de objetos PDF repetida;
- paginação/layout sem padrão institucional único.

### 1.4 Onde CSV/XLSX são gerados

- Relatórios gerais:
  - `GET /relatorios/export.csv`
  - `GET /relatorios/export.xlsx`
  - Implementação em `src/app/reports/routes.py`, reaproveitando `build_csv`/`build_xlsx` de `src/app/reports/exporters.py`.
- Entregas por evento:
  - `GET /entregas/eventos/{event_id}/export.csv`
  - `GET /entregas/eventos/{event_id}/export.xlsx`
  - `GET /entregas/eventos/{event_id}/criancas/export.xlsx`

### 1.5 Acesso ao usuário autenticado

Padrão já existente no projeto:

- em views HTML: `request.state.user` (ex.: context processors em `main.py`, `reports/routes.py`, `deliveries/routes.py`);
- em endpoints protegidos: dependências `require_permissions(...)`/`require_roles(...)` retornando `current_user: User`.

## 2) Inventário de endpoints de relatório existentes

### 2.1 Prefixo `/relatorios/*`

- `GET /relatorios`
- `GET /relatorios/export.csv`
- `GET /relatorios/export.xlsx`

### 2.2 Prefixo `/entregas/*`

- `GET /entregas/eventos/{event_id}/export.csv`
- `GET /entregas/eventos/{event_id}/export.xlsx`
- `GET /entregas/eventos/{event_id}/export.pdf`
- `GET /entregas/eventos/{event_id}/criancas/export.xlsx`
- `GET /entregas/eventos/{event_id}/criancas/export.pdf`

### 2.3 Endpoints unitários de export

- `GET /familias/{family_id}/export.pdf`

### 2.4 Lacunas vs objetivo do Sprint 6

Não existem ainda:

- `/relatorios/familias.pdf`
- `/relatorios/cestas.pdf`
- `/relatorios/criancas.pdf`
- `/relatorios/encaminhamentos.pdf`
- `/relatorios/equipamentos.pdf`
- `/relatorios/pendencias.pdf`
- `/pessoas/{id}/export.pdf`

## 3) Divergências de layout identificadas

- Ausência de cabeçalho institucional completo (nome sistema + igreja + metadados padronizados).
- Ausência de rodapé com paginação "Página X de Y".
- Estilos e estrutura de tabela diferentes entre relatórios.
- Sem seções formais (table/text) reutilizáveis.

## 4) Decisão técnica final

Adotar um **motor central único** em `src/app/pdf/report_engine.py`:

- API principal: `generate_report_pdf(title, month, year, sections, metadata) -> bytes`.
- Mantém abordagem sem dependência externa (bytes PDF), porém com layout institucional padronizado.
- Reutilização por todos os endpoints `.pdf`.

## 5) Impacto de refatoração

- Refatorar endpoints PDF existentes (`familias`, `entregas/eventos`, `entregas/eventos/.../criancas`) para o motor único.
- Criar novos endpoints PDF de relatórios agregados e pessoa em situação de rua.
- Preservar endpoints CSV/XLSX existentes e suas regras de permissão.
- Atualizar documentação:
  - `docs/PDF_ENGINE.md`
  - `README.md`
  - `RELATORIO_FINAL_CONFORMIDADE.md`

## 6) Plano de implementação após análise

1. Implementar `report_engine.py` (cabeçalho/corpo/rodapé/paginação).
2. Adaptar módulos `app.pdf` para expor o novo motor.
3. Refatorar endpoints PDF existentes para usar `generate_report_pdf`.
4. Criar endpoints PDF faltantes do Sprint 6.
5. Incluir totalizadores automáticos nas seções de relatório agregado.
6. Criar testes automatizados de cobertura PDF + regressão CSV/XLSX.
7. Atualizar documentação final.
