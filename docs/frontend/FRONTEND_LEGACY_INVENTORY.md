# Inventário do Frontend Legado

## 1) Localização do frontend antigo

- Frontend legado identificado no app Python:
  - `igreja_dashboard_python/templates/` (Jinja2/SSR)
  - `igreja_dashboard_python/static/` (assets estáticos)
- Após reorganização, foi movido para:
  - `frontend/legacy/igreja_dashboard_python/templates/`
  - `frontend/legacy/igreja_dashboard_python/static/`

## 2) Framework/stack do legado

- Renderização SSR via **FastAPI + Jinja2Templates**.
- Servidor de assets via **FastAPI StaticFiles**.
- Sem frontend SPA dedicado (React/Vue) e sem bundler JS moderno detectado.

## 3) Dependências principais detectadas

Origem: `igreja_dashboard_python/pyproject.toml`.

- `fastapi`
- `jinja2`
- `uvicorn`
- `python-multipart`
- `httpx`

Não foi identificado `package.json` no legado (sem Vite/Webpack no frontend antigo).

## 4) Rotas/telas legadas existentes (amostra principal)

- Login/recuperação: `login.html`, `auth_forgot_password.html`, `auth_reset_password.html`
- Dashboard: `dashboard/dashboard.html`
- Famílias: `families_list.html`, `family_form.html`, `family_detail.html`, `family_wizard_step.html`
- Pessoas de rua: `street/street_people_list.html`, `street/street_person_detail.html`
- Crianças: `children_list.html`, `children_form.html`, `children_detail.html`
- Entregas/Eventos: `deliveries_list.html`, `event_children_list.html`
- Equipamentos: `equipment_list.html`, `equipment_form.html`, `equipment_detail.html`, `loan_form.html`
- Admin: `admin_users.html`, `admin_user_form.html`, `admin_config.html`, `admin_audit.html`

## 5) Gap analysis vs `docs/SCREEN_RULES.md`

| Regra em SCREEN_RULES | Legado | Gap |
|---|---|---|
| Sidebar desktop + menu hambúrguer mobile obrigatório | Parcial | Alguns templates não aplicam layout único consistente. |
| Busca global no topo em telas internas | Parcial | Busca existe em fluxo específico, não padronizada em todas as telas internas. |
| Botão flutuante “Novo” com 4 atalhos fixos | Não evidenciado de forma global | Necessário padronizar no novo frontend. |
| Chips de alerta (4 tipos fixos) | Parcial | Alertas existem em fluxos, sem componente único padronizado. |
| Timeline obrigatória em Pessoa e Família | Parcial | Histórico aparece em partes do fluxo, sem componente consolidado único. |
| Rotas mínimas padronizadas | Parcial | Existem rotas equivalentes, porém com nomes/paths legados divergentes em alguns módulos. |
| Permissões por perfil (voluntário/pastoral/admin) | Parcial | Regras existem no backend, mas UX de negação/padrão de tela precisa padronização. |

## 6) Conclusão de auditoria rápida

O legado cobre a maior parte dos módulos funcionais, porém com inconsistências de nomenclatura/layout frente ao padrão fixado em `SCREEN_RULES.md`. A estratégia adotada foi isolar o legado em `frontend/legacy` e scaffoldar frontend web em PHP com rotas/títulos alinhados à constituição de telas.
