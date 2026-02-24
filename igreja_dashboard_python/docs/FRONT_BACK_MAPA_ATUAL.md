# FRONT_BACK_MAPA_ATUAL

## 1) Stack identificado (auditoria)
- **Front**: SSR com **FastAPI + Jinja2 + Bootstrap**, com navegação responsiva via `navbar-expand-lg` e botão hamburger no mobile.
- **Back**: FastAPI com rotas em `main.py` + routers (`dashboard`, `deliveries`, `reports`, `closures`, `history`).
- **Auth/RBAC**: JWT em cookie (`access_token`) e header Bearer; permissões por role (`Admin`, `Operador`, `Leitura`).
- **DB**: SQLAlchemy + Alembic, com suporte SQLite/PostgreSQL conforme `alembic` e settings.

## 2) Telas/rotas existentes (front SSR)

| Módulo | Tela | URL | Status |
|---|---|---|---|
| Auth | Login | `/login` | ✅ |
| Auth | Esqueci senha | `/password/forgot` | ✅ |
| Auth | Reset senha | `/password/reset` | ✅ |
| Dashboard | Painel | `/dashboard` | ✅ |
| Famílias | Lista | `/familias` | ✅ |
| Famílias | Wizard | `/familias/nova/step/{step}` | ✅ |
| Famílias | Detalhe | `/familias/{id}` | ✅ |
| Famílias | PDF | `/familias/{id}/export.pdf` | ✅ |
| Pessoas | Lista/Detalhe (rua) | `/rua`, `/rua/{id}` | ✅ |
| Pessoas | Alias de navegação | `/pessoas` | ✅ (novo alias) |
| Crianças | Lista/CRUD | `/criancas`, `/criancas/nova`, `/criancas/{id}/edit` | ✅ |
| Entregas | Eventos SSR | `/entregas` | ✅ (novo) |
| Entregas | Lista crianças evento | `/entregas/eventos/{id}/criancas` | ✅ |
| Equipamentos | Lista/CRUD | `/equipamentos` + subrotas | ✅ |
| Relatórios | Tela mensal | `/relatorios` | ✅ |
| Admin | Usuários | `/admin/users` | ✅ |
| Admin | Alias usuários | `/admin/usuarios` | ✅ (novo alias) |
| Admin | Config | `/admin/config` | ✅ |
| UX | Busca global | `/busca` | ✅ |

## 3) Endpoints (backend) - resumo

| Domínio | Endpoints principais |
|---|---|
| Auth | `POST /login`, `POST /auth/login` (novo), `POST /password/forgot`, `POST /password/reset`, `GET /logout` |
| Dashboard | `GET /dashboard` |
| Famílias | `GET /familias`, `POST /familias/nova`, `POST /familias/{id}/editar`, `GET /familias/{id}/export.pdf` |
| Pessoas | `GET /rua`, `POST /rua/nova`, `POST /rua/{id}/atendimentos`, `POST /rua/{id}/encaminhamentos`, `GET /pessoas/{id}/export.pdf` |
| Crianças | `GET/POST/POST-delete` em `/criancas...` |
| Entregas | `POST /entregas/eventos`, `GET /entregas/eventos` (novo), `POST /entregas/eventos/{id}/convidar`, `POST /entregas/eventos/{id}/retirada/{family_id}`, `POST /entregas/eventos/{id}/close` (novo), exports |
| Equipamentos | `/equipamentos/*`, empréstimo/devolução |
| Relatórios | `/relatorios`, exports CSV/XLSX/PDF |
| UX | `GET /timeline` (novo), `GET /busca` |

## 4) Gaps encontrados na auditoria
1. Não havia rota SSR dedicada para `/entregas` (menu operacional). **Fechado**.
2. Não havia alias de navegação `/pessoas` (fluxo cliente). **Fechado** com redirect para `/rua`.
3. Não havia alias `/admin/usuarios`. **Fechado**.
4. Não havia `GET /entregas/eventos` e `POST /entregas/eventos/{id}/close`. **Fechado**.
5. Não havia endpoint agregador explícito de timeline. **Fechado** com `GET /timeline?family_id=...|person_id=...`.
