# ADR-0001 — Estratégia de migração do frontend legado para frontend/ e stack PHP

- Status: Aceito (técnico)
- Data: 2026-02-25

## Contexto

O repositório atual executa backend/API em PHP custom (`public/index.php` + `src/Http/Kernel.php`) e contém frontend legado SSR em FastAPI/Jinja2 (`igreja_dashboard_python/templates`).

A solicitação exige frontend novo em stack PHP alinhado ao mapa de telas de `docs/SCREEN_RULES.md`, sem quebrar execução do repositório.

## Opções avaliadas

### Opção A — Introduzir aplicação Laravel completa no root imediatamente
- Prós: aderência total ao target Laravel + Blade/Vite/Tailwind.
- Contras: alto risco de regressão no bootstrap atual, mudanças amplas de infraestrutura, impacto em testes existentes.

### Opção B — Isolar legado + scaffold web PHP compatível com padrões Laravel (rotas/views) no app atual
- Prós: baixo risco, preserva execução atual, permite evolução incremental para Laravel mantendo rotas/telas padronizadas.
- Contras: não entrega framework Laravel completo nesta etapa; exige etapa futura de convergência.

## Decisão

Adotada **Opção B** nesta etapa: isolamento do legado em `frontend/legacy` e criação de camada web PHP com estrutura `routes/web.php` + `resources/views/*` + stubs por tela conforme `SCREEN_RULES.md`.

## Consequências

- Repositório permanece executável no entrypoint atual.
- Rotas web mínimas ficam scaffoldadas com estados e componentes globais de UX.
- Convergência final para Laravel full stack fica planejada como próxima evolução sem ruptura.
