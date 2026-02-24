# ARQUITETURA

## Stack

- FastAPI + Jinja2 SSR
- SQLAlchemy 2.x + Alembic
- Banco principal: SQLite (dev) / PostgreSQL (produção)
- Autenticação por JWT em cookie HTTPOnly
- RBAC por papéis e permissões
- Geração de PDF institucional por motor central

## Camadas

- `src/app/main.py`: rotas web principais e composição da aplicação
- `src/app/*/routes.py`: módulos especializados (dashboard, relatórios, entregas, fechamento)
- `src/app/models`: entidades de domínio
- `src/app/eligibility`: motor de elegibilidade
- `src/app/closures`: fechamento mensal, relatório oficial e snapshots
- `src/app/history`: histórico mensal e séries comparativas
- `src/app/services/audit.py`: trilha de auditoria

## Persistência de artefatos

- PDFs de fechamento e relatório oficial em `data/reports`.
- Hash SHA256 calculado e persistido para relatório oficial mensal.
