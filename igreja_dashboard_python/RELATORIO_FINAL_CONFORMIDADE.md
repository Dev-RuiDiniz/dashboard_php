# RELATÓRIO FINAL DE CONFORMIDADE — Pós-Sprints 0–5

Data: 2026-02-18
Projeto: Sistema Web de Gestão da Ação Social

## Metodologia
- Leitura técnica de código (rotas, modelos, templates, migrações).
- Execução da suíte automatizada (`pytest` e `pytest --cov=src/app --cov-report=term-missing`).
- Consolidação por módulo com status de conformidade ao escopo consolidado.

> Nota: houve 1 falha em teste de convite automático por vulnerabilidade (`tests/test_delivery_events.py::test_invite_auto_by_vulnerability`), portanto o status geral operacional é **parcial**.

## Matriz de conformidade

| Módulo | Status | Evidência | Observação |
|--------|--------|-----------|------------|
| Autenticação | ✅ Conforme | Rotas login/logout/reset; lockout/rate-limit; testes `test_sprint4_security_ux_pdf.py` e `test_auth.py` | Perfis implementados como Admin/Operador/Leitura (nomenclatura difere de Voluntário/Admin/Pastoral). |
| Dashboard | 🟡 Parcial | Dashboard com cards, alertas e tabela de elegíveis | Não contempla exatamente todos cards/filtros do escopo macro em um único painel. |
| Famílias | ✅ Conforme | CRUD, wizard, bloqueio CPF duplicado, CEP, histórico, PDF de ficha, vínculos | Fluxo operacional principal disponível. |
| Ficha Social (Pessoas) | 🟡 Parcial | Cobertura forte para famílias e pessoas em situação de rua | Não há módulo explícito único chamado “Ficha Social” com todas seções exigidas no formato do escopo. |
| Crianças | ✅ Conforme | CRUD de crianças, filtro por idade, lista por evento, export XLSX/PDF | Export Excel/PDF coberto; integração com evento implementada. |
| Entregas | 🟡 Parcial | Evento, convite manual/automático, código de retirada, assinatura, encerramento, export CSV/XLSX/PDF(crianças) | Falha automatizada atual no convite automático por vulnerabilidade indica regressão pontual. |
| Equipamentos | ✅ Conforme | Cadastro, código/status, empréstimo, devolução, histórico e pendências | Fluxo ponta a ponta implementado com trilha em dashboard/relatórios. |
| Relatórios | ✅ Conforme | Filtros ano/mês e export CSV/XLSX/PDF universal com layout institucional padronizado | Relatórios PDF universais implementados e centralizados no motor único. |
| Usuários e Config | 🟡 Parcial | CRUD usuários, perfis RBAC, configurações de elegibilidade/limites, termo de consentimento | Categorias de encaminhamento parametrizadas não aparecem como módulo dedicado de configuração. |
| Elegibilidade automática | 🟡 Parcial | Engine de elegibilidade + configurações administrativas + seção no dashboard | Uma regressão de teste impede afirmar conformidade total até correção. |
| LGPD e rastreabilidade | ✅ Conforme | Consentimento obrigatório, termo versionado, audit_logs, RBAC, backup documentado | Manter monitoramento contínuo de logs para prevenção de exposição sensível. |
| Fechamento mensal (snapshot + PDF) | ✅ Conforme | Tabela `monthly_closures`, snapshot consolidado, PDF de fechamento persistido, lock retroativo e rotas admin de consulta/download | Governança contábil/social oficial implementada para competência mensal. |
| Relatório mensal consolidado oficial | ✅ Conforme | Snapshot oficial, PDF oficial com assinatura administrativa, hash SHA256, imutabilidade e endpoints admin dedicados | Prestação de contas institucional com trilha de auditoria e verificação criptográfica. |

## Resultado consolidado

- **Conformidade geral:** 🟡 **Parcial**.
- **Motivos principais de parcialidade:**
  1. Divergência arquitetural de frontend (SSR Jinja2 vs React esperado no escopo).
  2. Falha automatizada atual no fluxo de convite automático por elegibilidade/vulnerabilidade.
  3. Alguns itens de escopo com cobertura funcional próxima, mas não idêntica no formato exigido (dashboard/ficha social).

## Lista de gaps e próximos passos recomendados

1. Corrigir regressão do convite automático em eventos de entrega e estabilizar suíte (`test_invite_auto_by_vulnerability`).
2. Decidir formalmente sobre estratégia de frontend:
   - manter SSR e atualizar escopo oficial, **ou**
   - migrar para React conforme arquitetura declarada.
3. Fechar lacunas de produto:
   - padronização da “Ficha Social” nas seções explicitadas no escopo;
   - validar/expandir configurações administrativas de categorias de encaminhamento.
4. Executar rodada de homologação manual guiada por perfil (Voluntário/Admin/Pastoral) em ambiente de staging com PostgreSQL.


## Atualização Sprint 8

- Relatório mensal consolidado oficial: ✅ Implementado.


## Atualização Sprint 9

- Histórico mensal + análise comparativa: ✅ Implementado.
