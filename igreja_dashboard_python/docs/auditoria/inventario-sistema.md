# Inventário técnico do sistema

## 1) Stack e estrutura do repositório

## Stack identificado
- Backend web: **FastAPI** com rotas SSR e API (`app/main.py`, routers dedicados).  
- Renderização: **Jinja2** (`templates/`).  
- ORM: **SQLAlchemy 2.x** (modelos em `app/models/`).  
- Migrações: **Alembic** (`alembic/versions/`).  
- Banco: **SQLite/PostgreSQL** conforme `DATABASE_URL`.  
- Testes: **pytest** (`tests/`).

## Pastas principais
- `app/`: domínio principal (modelos, rotas, serviços, segurança, relatórios, dashboard).  
- `templates/`: telas SSR (famílias, equipamentos, rua, relatórios, admin etc.).  
- `alembic/versions/`: evolução de schema.  
- `docs/`: documentação funcional/técnica.  
- `tests/`: testes automatizados por módulo.  
- `scripts/`: backup/restore/migração de banco.  
- `static/`: assets.  
- `api/`: ponto de entrada alternativo para deploy.

## 2) Como rodar localmente

### Fluxo Python local
1. Criar venv e instalar dependências.
2. Rodar migrations.
3. Subir app com Uvicorn.

Referência direta no repositório: `README.md`.

### Fluxo Docker Compose
- Serviço `db` (PostgreSQL 16).
- Serviço `web` com `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000`.

Referência: `docker-compose.yml`.

## 3) Mapeamento técnico-base por camada

## 3.1 Modelos/ORM (núcleo auditado)
- Famílias/dependentes/crianças/cestas/visitas: `app/models/family.py`.  
- Equipamentos/empréstimos: `app/models/equipment.py`.  
- Moradores de rua/atendimentos/encaminhamentos: `app/models/street.py`.  
- Entregas por evento/auditoria: `app/models/delivery.py`.

## 3.2 Migrações de schema relacionadas ao escopo
- `0003_family_dependent.py`: `families`, `dependents`.  
- `0004_equipment_loans.py`: `equipment`, `loans`.  
- `0005_food_baskets.py`: `food_baskets`.  
- `0006_street_domain.py`: `street_people`, `street_services`, `referrals`.

## 3.3 Endpoints e rotas (domínio da auditoria)
- Famílias: `/familias*` (cadastro, edição, detalhe, dependentes, cestas, visitas).  
- Equipamentos: `/equipamentos*` (cadastro, edição, empréstimo, devolução).  
- Rua: `/rua*` + encaminhamentos/atendimentos.  
- CEP: `/api/cep/{cep}`.

Rotas localizadas principalmente em `app/main.py`.

## 3.4 Telas e consumo de endpoints
- `templates/family_form.html` + `POST /familias/nova`; integração CEP via `GET /api/cep/{cep}`.  
- `templates/family_detail.html` + ações `POST /familias/{id}/cestas` e `POST /familias/{id}/visitas`.  
- `templates/equipment_form.html`, `templates/loan_form.html` + rotas de equipamentos/empréstimos.  
- `templates/street/street_person_form.html`, `templates/street/street_person_detail.html` + rotas de rua.

## 4) Observações de arquitetura relevantes para aderência
- Sistema é majoritariamente **SSR** (não há API REST JSON completa por módulo).  
- Há validações de CPF e CEP no backend, mas muitas regras do documento do cliente são de domínio específico (campos/enums/contadores) e não existem no schema atual.  
- O módulo de cestas no sistema está modelado como **registro mensal por referência** (`reference_month/reference_year/status`) e não como “ficha de entrega com frequência configurável, última retirada com responsável e status Apta/Já beneficiada/Atenção”.
