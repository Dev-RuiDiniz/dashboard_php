# Auditoria de aderência — Backend (regras + endpoints)

## 1) Endpoints existentes x necessários (por módulo do PDF)

## 1.1 Famílias

| Necessário (PDF) | Existe no backend? | Evidência | Status |
|---|---|---|---|
| CRUD de famílias | Parcial (Create/Read/Update + inativação; sem delete físico) | rotas `/familias*` em `app/main.py` | ⚠️ |
| CRUD de dependentes | Sim (create/update/remove) | `/familias/{id}/dependentes/*` | ✅ |
| Validação CPF e duplicidade | Sim | `_validate_cpf`, `_cpf_conflict` | ✅ |
| Validação RG/formato | Não dedicada | `responsible_rg` sem validador específico | ❌ |
| Cálculo de idade | Função utilitária existe, sem uso explícito para regra de domínio da ficha | `_calculate_age` | ⚠️ |
| Cálculo de renda total | Não existe | sem serviço/agregador específico | ❌ |
| “Necessita visita” com alerta | Parcial via módulo de visitas pendentes/atraso | `VisitRequest` + `_build_visit_alerts` | ⚠️ |
| Trilha mínima de quem/quando | Parcial (created_at em entidades; nem toda mutação registra user_id) | modelos + `AuditLog` em ações críticas | ⚠️ |

## 1.2 Cestas básicas

| Necessário (PDF) | Existe? | Evidência | Status |
|---|---|---|---|
| CRUD cestas | Parcial (create/update/delete) | `/familias/{id}/cestas*` | ⚠️ |
| Data automática de entrega | Não implementado conforme PDF | registro por mês/ano | ❌ |
| Quantidade padrão e frequência mensal configurável | Não | sem campos dedicados | ❌ |
| Status Apta/Já beneficiada/Atenção | Não | enum atual Entregue/Pendente/Cancelada | ❌ |
| Última retirada com responsável | Não | sem campo/rota dedicada | ❌ |

## 1.3 Equipamentos / Empréstimos

| Necessário (PDF) | Existe? | Evidência | Status |
|---|---|---|---|
| CRUD equipamentos | Parcial (create/read/update; sem delete) | `/equipamentos*` | ⚠️ |
| CRUD empréstimos | Parcial (create + devolução; sem update/delete explícitos) | `/equipamentos/{id}/emprestimo`, `/devolver` | ⚠️ |
| Datas automáticas retirada/devolução | Parcial | retirada manual; devolução registra `date.today()` | ⚠️ |
| Prazo obrigatório de devolução | Não | `due_date` opcional | ❌ |
| Status e alertas de vencimento | Parcial | status disponível/emprestado/indisponível + destaque visual de atraso | ⚠️ |
| Histórico de uso | Sim | relacionamento `loans` e tela de detalhe | ✅ |

## 1.4 Moradores de rua

| Necessário (PDF) | Existe? | Evidência | Status |
|---|---|---|---|
| CRUD de moradores de rua | Parcial (create/read + atendimentos + encaminhamentos; sem update/delete pessoa) | `/rua*` | ⚠️ |
| Campos estruturados de documentos/tempo rua/necessidades/decisão espiritual | Não | schema não possui colunas específicas | ❌ |
| Encaminhamentos por categorias oficiais | Parcial (há encaminhamento, mas texto livre) | `Referral.recovery_home` | ⚠️ |
| Consentimento + assinatura + data | Parcial | consentimento e timestamp; assinatura nominal ausente | ⚠️ |

## 2) Regras automáticas e validações transversais

| Regra do escopo | Estado | Evidência |
|---|---|---|
| CPF com validação de dígitos e normalização | Implementada | `_validate_cpf` |
| Duplicidade CPF (família/dependente/rua) | Implementada | `_cpf_conflict`, `_validate_street_cpf` |
| CEP com integração | Implementada | `GET /api/cep/{cep}` + `fetch_address_by_cep` |
| Datas automáticas de retirada/devolução quando aplicável | Parcial | devolução automática no ato; retirada manual |
| Status calculados (Apta/Já beneficiada/Atenção) | Não implementado | não há engine para esse status |
| Alerta prazo vencido devolução | Parcial | há indicação visual no detalhe de equipamento |
| Cálculo idade/renda total | Parcial/ausente | idade utilitária; renda total inexistente |
| Trilha “quem fez” + “quando” | Parcial | `created_at` amplo, `AuditLog` não cobre todo CRUD |

## 3) Gaps e plano de correção por prioridade

## P0
1. Criar contratos de dados/endpoints aderentes às tabelas do PDF para Famílias, Cestas e Rua.  
2. Introduzir status de cesta conforme regra de elegibilidade da família (Apta/Já beneficiada/Atenção).  
3. Completar schema e API de rua com campos de acompanhamento e decisão espiritual.

## P1
1. Tornar empréstimo aderente: prazo obrigatório, condição na devolução, status manutenção.  
2. Padronizar enum/catálogo de encaminhamentos (CRAS/CAPS/UBS etc.).

## P2
1. Expandir auditoria para trilha completa de CRUD por módulo.  
2. Expor API REST JSON oficial (atualmente predominam handlers SSR/form).

## 4) Arquivos-alvo sugeridos para implementação futura
- `app/models/family.py`, `app/models/equipment.py`, `app/models/street.py`  
- `app/main.py` (rotas/form handlers e validações)  
- `alembic/versions/*` (novas migrations)  
- `templates/*` para refletir novos contratos de backend.
