# Relatório de Auditoria Final

## Escopo e método
Auditoria técnica completa do repositório PHP em comparação com:
1. `Especificacao_Sistema_Igreja_Social_PHP_MySQL.docx` (fonte de verdade final desta auditoria).
2. `docs/DB_RULES_MYSQL.md`.
3. `docs/SCREEN_RULES.md`.

Base de validação: leitura de rotas web/API, stores de domínio, migrations SQL, autenticação/RBAC, exportações e execução do pipeline de checks automatizados (`bash scripts/ci_checks.sh`).

> **Conflito normativo identificado:** `docs/DB_RULES_MYSQL.md` define o PDF como “fonte de verdade única”, enquanto esta auditoria foi formalmente mandatada para usar o DOCX como fonte de verdade final. Conflito registrado em ADR separado (`docs/decisions/ADR-0002-source-of-truth-conflict-docx-vs-pdf.md`).

---

## 1) Conformidade geral (% estimado)
- **Estimativa de aderência global ao DOCX:** **61%**.
- Critério: cobertura funcional macro existente, porém com lacunas importantes em modelagem de dados, telas operacionais reais, perfis RBAC completos, visitas, recuperação de senha com token e regras avançadas de relatórios.

Status: **Parcial**.

---

## 2) Módulos implementados vs especificação

| Módulo | Status | Evidência resumida |
|---|---|---|
| Autenticação | Parcial | Login, JWT, lockout e `/me` implementados; recuperação de senha por token/expiração não implementada. |
| Dashboard | Parcial | Existe rota web `/dashboard` apenas como stub e `/reports/summary` para métricas básicas. |
| Famílias | Parcial | CRUD básico de família/dependentes/crianças com validação CPF; faltam campos e funcionalidades completas do DOCX. |
| Pessoas acompanhadas/ficha social | Parcial | Cadastro básico em `street/people` e encaminhamentos simples; ficha social completa e timeline não implementadas. |
| Crianças | Parcial | CRUD básico existe; lista automática por evento não encontrada. |
| Entregas de cestas | Parcial | Eventos, convites, retirada com assinatura e bloqueio mensal implementados; faltam regras de status detalhadas/ticket sequencial e operação completa de telas. |
| Equipamentos | Parcial | Cadastro/empréstimo/devolução e status principal implementados; faltam alertas operacionais explícitos e campos completos do DOCX. |
| Visitas e pendências | Não implementado | Não há rotas/API/tabela de visitas no código/migrations atuais. |
| Usuários e configurações admin | Parcial | Gestão real de usuários não implementada (apenas store em memória); configurações de elegibilidade existem parcialmente. |

---

## 3) Telas implementadas vs especificação

| Tela oficial | Status | Observação |
|---|---|---|
| Login | Parcial | Rota web stub `/login`; autenticação efetiva via API `/auth/login`. |
| Recuperar senha | Divergente | Apenas stub de tela; fluxo de token/expiração ausente. |
| Dashboard | Parcial | Stub web + summary API, sem dashboard operacional completo com cards/alertas reais. |
| Famílias (lista/nova/detalhe) | Parcial | Rotas web existem, porém como stubs genéricos. |
| Pessoas (lista/novo atendimento/detalhe) | Parcial | Rotas web stubs; backend não cobre ficha social completa. |
| Crianças (lista/cadastro/editar) | Parcial | Rotas web stubs e backend básico. |
| Entregas (eventos/novo/convidados/crianças) | Parcial | Rotas web stubs e APIs principais implementadas. |
| Equipamentos (lista/novo/emprestimos) | Parcial | Rotas web stubs e APIs de domínio existentes. |
| Visitas | Não implementado | Ausência de tela/rota/API específica de visitas. |
| Usuários/Config admin | Parcial | Rotas web stubs; sem CRUD persistente de usuários. |

---

## 4) Banco de dados (campos faltando / extras / divergentes)

### 4.1 Cobertura atual
- Migrations existentes cobrem subconjunto: `families`, `dependents`, `children`, `street_residents`, `street_referrals`, `delivery_events`, `delivery_invites`, `delivery_withdrawals`, `equipments`, `equipment_loans`, `eligibility_settings`.

### 4.2 Principais lacunas frente ao DOCX
- **Não implementadas** tabelas esperadas no DOCX: `users` (persistente), `people` completa, `social_records`, `referrals` (modelo da ficha social), `spiritual_followups`, `visits`, `audit_logs` relacional.
- **Families simplificada**: faltam muitos campos socioeconômicos/endereço/pendências detalhadas.
- **Entregas divergentes**: modelo usa `delivery_invites`/`delivery_withdrawals` e não possui `ticket_number` sequencial por evento como no DOCX.
- **Equipamentos parcialmente aderente**: ausência de `return_date`, `person_id` opcional e alguns campos de criação exigidos.

Status: **Divergente**.

---

## 5) Regras de negócio (implementadas / ausentes)

| Regra | Status | Observação |
|---|---|---|
| CPF único família | OK | Implementado com validação e bloqueio de duplicidade. |
| CPF único pessoa quando informado | Parcial | Modelo de pessoa/ficha não completo. |
| Bloqueio mensal de cesta | OK | Bloqueio por família/mês implementado em retiradas. |
| Ticket sequencial por evento | Não implementado | Código de retirada aleatório, não ticket sequencial imutável. |
| Fluxo de status de entrega `nao_veio->presente->retirou` | Parcial | Não há máquina de estados completa exposta. |
| Assinatura simples na retirada | OK | Exigência de assinatura ao retirar implementada. |
| Consistência de status de equipamento | OK | Empréstimo/devolução atualizam status disponível/emprestado/manutenção. |
| Alertas operacionais (docs/visita/desatualização/atraso) | Parcial | Não há módulo de alertas completo; parte inferida em summary e regras de empréstimo. |
| Cálculo de renda familiar por membros | Não implementado | Campos/routine de soma ausentes. |
| Consentimento obrigatório na ficha social | Parcial | Há consentimento na entidade street simplificada, não na ficha social completa do DOCX. |

---

## 6) Permissões por perfil

Status: **Parcial**.

- Implementado: autenticação JWT; autorização de escrita para `Admin` e `Operador`; endpoint admin protegido.
- Divergências:
  - Perfis oficiais (`admin`, `voluntario`, `pastoral`, `viewer`) não estão mapeados como no DOCX (há `Admin`, `Operador`, `Leitura`).
  - Não há matriz explícita por módulo + ação (`ver/criar/editar/excluir`) para todos os domínios.
  - `Pastoral` não identificado no runtime.

---

## 7) Relatórios e exportações

Status: **Parcial**.

- Implementado: exportações CSV/XLSX/PDF de famílias e endpoint de resumo.
- Lacunas:
  - Relatórios mensais completos por bairro/status/módulo não implementados.
  - Relatórios de encaminhamentos, pendências e equipamentos em todos estados não evidenciados como saídas formais.
  - Integração explícita com PHPSpreadsheet/Dompdf/mPDF não comprovada (há gerador simplificado interno).

---

## 8) Performance e índices

Status: **Parcial**.

- Positivo: migrations possuem índices básicos em FKs e campos críticos (CPF, nomes, status, datas em subset).
- Lacunas: não há evidência de estratégia global de índices para todos filtros oficiais (bairro/cidade/pendências/último atendimento), nem análise de plano de execução para cenários de produção.

---

## 9) Segurança (validação, auth, permissões, CSRF, sanitização)

Status: **Parcial**.

- Positivo: JWT, lockout por tentativas, headers de segurança, prepared statements no acesso MySQL (via stores PDO), checagens de autorização em rotas de escrita.
- Divergente crítico:
  - `UserStore` usa senha em texto puro para usuários bootstrap (não hash forte conforme DOCX).
  - Recuperação de senha com token/expiração ausente.
  - Controles de sessão web (regeneração explícita de session_id/cookies de sessão) não aplicáveis no mesmo nível do requisito, pois arquitetura atual é majoritariamente stateless/JWT + stubs SSR.

---

## 10) Código morto / arquivos não utilizados

Status: **Parcial**.

- Há diretório de legado Python (`frontend/legacy/igreja_dashboard_python`) e projeto paralelo completo (`igreja_dashboard_python/`) no mesmo repositório.
- Esses artefatos aparentam histórico/migração, não runtime principal PHP; porém ocupam grande superfície e elevam risco de confusão operacional.
- Não foi aplicada remoção automática por risco de perda de rastreabilidade histórica sem critério formal de retenção.

---

## 11) Dívida técnica

1. Matriz RBAC incompleta frente à especificação oficial.
2. Web frontend ainda majoritariamente em telas stub.
3. Modelo de dados muito reduzido frente ao DDL oficial do DOCX.
4. Ausência de módulo de visitas/pendências completo.
5. Fluxo de recuperação de senha incompleto.
6. Senhas bootstrap sem hash forte.

Status: **Divergente**.

---

## 12) Riscos para produção

| Risco | Nível | Impacto |
|---|---|---|
| Dados insuficientes para operação social completa (schema parcial) | Alto | Perda de rastreabilidade e incapacidade de cumprir fluxos previstos. |
| Segurança de credenciais bootstrap em texto puro | Alto | Violação de requisito de segurança e aumento de risco de comprometimento. |
| Ausência de visitas/pendências completas | Médio/Alto | Falha operacional em acompanhamento social e auditoria de campo. |
| Frontend predominantemente stub | Alto | Operação real limitada e baixa prontidão de uso institucional. |
| Conflito formal de fonte de verdade (DOCX vs PDF em DB_RULES) | Médio | Decisões contraditórias de evolução sem governança unificada. |

---

## 13) Checklist final de aderência

| Item | Status |
|---|---|
| Autenticação básica | OK |
| Recuperação de senha tokenizada | Não implementado |
| Dashboard operacional completo | Parcial |
| Famílias completo (campos + fluxos) | Parcial |
| Ficha social completa | Não implementado |
| Crianças com fluxo por evento completo | Parcial |
| Entregas com ticket sequencial e operação completa | Parcial |
| Equipamentos com alertas completos | Parcial |
| Visitas e pendências | Não implementado |
| Usuários admin persistentes | Parcial |
| RBAC por módulo/ação completo | Parcial |
| Relatórios mensais completos | Parcial |
| Segurança aderente ao DOCX | Parcial |
| Deploy/backup/scheduler formalizado | Parcial |

---

## Auto-verificação final (obrigatória)

- **% estimado de aderência à especificação:** **61%**.
- **O sistema está pronto para produção?** **Não**.
- **Existem divergências críticas?** Sim:
  1. Segurança de senhas bootstrap sem hash forte.
  2. Ausência de módulo de visitas/pendências completo.
  3. Ausência de ficha social/modelagem relacional completa (social_records/referrals/spiritual_followups).
  4. Frontend operacional majoritariamente em stubs.
- **Existem riscos técnicos relevantes?** Sim, especialmente risco de compliance funcional e segurança.
- **Próximo passo recomendado:** executar plano de correções críticas priorizado (arquivo `PLANO_CORRECOES_CRITICAS.md`) com foco em segurança+schema+RBAC+visitas antes de homologação final.

