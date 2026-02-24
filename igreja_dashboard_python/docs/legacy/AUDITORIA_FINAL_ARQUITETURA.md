# Auditoria Final de Arquitetura (Pós-Sprints 0–5)

Data: 2026-02-18

## 1) Inventário técnico real implementado

### Stack identificada no código
- **Frontend real:** SSR com **Jinja2 + Bootstrap** (não há SPA React no repositório).
- **Backend:** **FastAPI**.
- **Banco de dados:** **SQLite por padrão** e **PostgreSQL suportado/esperado para produção**.
- **ORM:** **SQLAlchemy 2.x** com migrações Alembic.
- **Auth:** **JWT** (python-jose), armazenado em cookie HTTPOnly.
- **Infra/Deploy:** Docker Compose (web + postgres), além de entrada para Vercel (`api/index.py` + `vercel.json`).

### Evidências (arquivos/dependências)
- `requirements.txt`/`pyproject.toml`: fastapi, jinja2, sqlalchemy, psycopg, python-jose.
- `src/app/main.py`: inicialização FastAPI + montagem de templates/rotas.
- `src/app/core/security.py`: criação/decodificação JWT.
- `src/app/core/auth_cookie.py`: cookie HTTPOnly para token.
- `docker-compose.yml`: serviço postgres e `DATABASE_URL` com `postgresql+psycopg`.

## 2) Comparação com arquitetura declarada no escopo

Arquitetura declarada para auditoria: **React + FastAPI + PostgreSQL + JWT**.

### Resultado
- **FastAPI:** ✅ conforme.
- **JWT:** ✅ conforme.
- **PostgreSQL:** 🟡 parcial (suportado e recomendado em produção, mas SQLite ainda é default de desenvolvimento).
- **React:** ❌ divergente (frontend atual é SSR em Jinja2, sem projeto React/Vite).

## 3) Mapeamento de estrutura de pastas solicitada

### Encontrado no repositório
- `src/`
  - `src/app/`
    - `db/`
    - `models/`
    - `dashboard/`
    - `deliveries/`
    - `reports/`
    - `security/`
    - `services/`
    - `eligibility/`
    - `pdf/`
- `api/`
- `alembic/` e `alembic/versions/`
- `templates/`
- `tests/`
- `docs/`

### Não encontrado como pasta raiz dedicada
- `frontend/` (não existe)
- `backend/` (não existe)
- `components/` (não existe como diretório de frontend moderno)
- `routes/` (há módulos de rotas dentro de `src/app/*`, não pasta raiz `routes/`)
- `migrations/` (equivalente no projeto é `alembic/versions/`)

## 4) Conclusão arquitetural

A base está consistente com uma arquitetura **monolítica web SSR em FastAPI**, com domínio e migrações organizados e boa cobertura de testes. Porém, **há divergência explícita do frontend previsto em React**, e o **uso de PostgreSQL não é o padrão local** (embora plenamente suportado para deploy).
