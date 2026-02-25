# Sistema de Gestão da Ação Social

## 1. Visão Geral

Plataforma web para gestão social institucional com foco em cadastro social, operação de entregas, empréstimo de equipamentos, geração de relatórios e governança mensal.

### O que o sistema resolve

- Centraliza o atendimento social em um único fluxo operacional.
- Padroniza prestação de contas com fechamento mensal e relatório oficial.
- Aumenta segurança e rastreabilidade com RBAC, auditoria e controles LGPD.

### Objetivo institucional

Oferecer gestão social segura, auditável e orientada por evidências para apoiar o trabalho de voluntários, administração e pastoral.

## 2. Arquitetura

### Stack real

- **Backend:** FastAPI
- **Renderização:** Jinja2 (SSR)
- **ORM:** SQLAlchemy 2.x
- **Migrações:** Alembic
- **Banco:** SQLite (local) / PostgreSQL (produção)
- **Auth:** JWT em cookie HTTPOnly + RBAC
- **Relatórios:** CSV/XLSX/PDF institucional

### Como rodar local

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
python -m uvicorn app.main:app --reload
```

> No Windows + PowerShell:
>
> ```powershell
> python -m venv .venv
> .\.venv\Scripts\Activate.ps1
> pip install -r requirements.txt
> alembic upgrade head
> python -m uvicorn app.main:app --reload
> ```

O comando de inicialização deve ser executado na raiz do projeto (onde está o `pyproject.toml`).

### Como rodar produção

1. Definir variáveis críticas (`DATABASE_URL`, `SECRET_KEY`, `APP_ENV=production`).
2. Executar migrações (`alembic upgrade head`).
3. Publicar com servidor ASGI compatível (ex.: Uvicorn/Gunicorn).
4. Garantir HTTPS e política de logs/auditoria ativa.

## 3. Perfis e Permissões

### Voluntário (Operador)

Pode operar famílias, crianças, entregas, equipamentos e relatórios operacionais conforme permissões de gestão.

**Fluxo típico**: login → dashboard → famílias/crianças → entregas/equipamentos → relatórios.

### Administrador

Tem todos os acessos operacionais e administrativos:

- gestão de usuários e configurações;
- gestão de consentimento LGPD;
- auditoria;
- fechamento mensal;
- geração do relatório oficial mensal.

### Pastoral (Leitura)

Acesso de consulta (dashboard, famílias, histórico e relatórios permitidos), sem ações de alteração de dados.

## 4. Fluxos Operacionais

### Criar família
`/familias` → novo cadastro (wizard) → salvar ficha social.

### Registrar atendimento social
Ficha da família/pessoa → registrar visita, serviço ou encaminhamento.

### Criar evento de entrega
`/entregas/eventos` → criar evento → convidar famílias (manual/automático).

### Operar evento no dia
Registrar retiradas com assinatura e exportar listas/relatórios do evento.

### Emprestar equipamento
`/equipamentos/{id}/emprestimo` → registrar empréstimo → devolver no retorno.

### Gerar relatórios
`/relatorios` com exportação CSV/XLSX/PDF e filtros por período.

### Fechar mês
`/admin/fechamento` → fechar mês (snapshot + PDF institucional).

### Gerar relatório oficial
Ainda em `/admin/fechamento` → gerar oficial (SHA256, assinatura e imutabilidade).

### Consultar histórico
`/historico` para comparação mensal e séries.

## 5. Relatórios e PDFs

- **PDF padrão institucional** para relatórios operacionais.
- **Fechamento mensal** com snapshot consolidado e arquivo persistido.
- **Relatório oficial mensal** com hash SHA256 e bloqueio de regeneração sem override.
- **Histórico comparativo** baseado em snapshots mensais.

## 6. Segurança e LGPD

- Consentimento LGPD ativo e administrável.
- Auditoria de ações críticas.
- RBAC por perfil e permissões.
- Reset de senha por token.
- Lockout e rate limit de login.

## 7. Backup e Manutenção

- Backup via scripts em `scripts/`.
- PDFs institucionais em `data/reports`.
- Restauração por rotina de banco e reprocessamento controlado.

## 8. Estrutura do Banco

Principais entidades:

- Usuários, papéis e permissões.
- Famílias, dependentes, crianças, cestas e visitas.
- Pessoas em situação de rua, serviços e encaminhamentos.
- Entregas por evento (convites, retiradas).
- Equipamentos e empréstimos.
- Fechamento mensal, snapshot e relatório oficial.
- Auditoria, consentimento e configurações do sistema.

## 9. Como Expandir para Multi-Unidade

Recomendações futuras:

1. Introduzir `unit_id` em entidades de domínio.
2. Segregar dados por unidade via RBAC contextual.
3. Parametrizar branding/documentos por unidade.
4. Consolidar relatórios por unidade e visão central.
5. Implementar trilha de auditoria com escopo por unidade.

---

## Documentação consolidada

- `docs/ARQUITETURA.md`
- `docs/MODULOS.md`
- `docs/FECHAMENTO_MENSAL.md`
- `docs/RELATORIO_OFICIAL_MENSAL.md`
- `docs/HISTORICO_MENSAL.md`
- `docs/LGPD.md`
- `docs/SEGURANCA.md`
- `docs/CONFIGURACOES.md`
- `docs/FLUXO_OPERACIONAL.md`
- `docs/ROTEIRO_HOMOLOGACAO.md`
- `docs/GUIA_DE_USO_DO_SISTEMA.md`

## Como usar por perfil (fluxo operacional resumido)

### Admin
1. Acesse `/login`.
2. Gerencie usuários em `/admin/usuarios` e parâmetros em `/admin/config`.
3. Acompanhe dashboard em `/dashboard` e relatórios em `/relatorios`.

### Operador
1. Cadastre e acompanhe famílias em `/familias`.
2. Registre pessoas/ficha social em `/pessoas` (alias de `/rua`).
3. Mantenha crianças em `/criancas`.
4. Execute eventos de entrega em `/entregas`.
5. Controle equipamentos em `/equipamentos`.

### Leitura
1. Use `/dashboard`, `/familias`, `/pessoas`, `/criancas`, `/relatorios` de acordo com permissões RBAC.
2. Utilize busca global pelo topo (`/busca?q=...`).

### Fluxos operacionais-chave
- Login/Reset: `/login`, `/password/forgot`, `/password/reset`.
- Entregas: criar/listar eventos (`/entregas`, `/entregas/eventos`), convidar, registrar retirada, encerrar evento.
- Timeline agregada (API): `GET /timeline?family_id=...` ou `GET /timeline?person_id=...`.

> Nota de migração: os diretórios `templates/` e `static/` foram isolados em `../frontend/legacy/igreja_dashboard_python/` e mantidos via symlink para compatibilidade.
