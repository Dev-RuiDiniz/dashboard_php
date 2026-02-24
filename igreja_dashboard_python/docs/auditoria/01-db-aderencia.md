# Auditoria de aderência — Banco de Dados (schema)

> Fonte funcional: checklist do cliente (PDF VersaoFinalSistemaWeb_Pib2026, págs. 1–4, conforme escopo desta sprint).  
> Fonte técnica: models + migrations do repositório.

## Legenda
- ✅ aderente
- ⚠️ parcial
- ❌ ausente/divergente

## 1) Famílias (PDF pág. 1–2)

| Requisito (PDF) | Coluna/tabela esperada | Encontrado no repo | Status | Evidência técnica |
|---|---|---|---|---|
| Identificação do responsável | `families.responsible_name` | Existe | ✅ | `app/models/family.py`, `alembic/versions/0003_family_dependent.py` |
| CPF com validação e unicidade | `families.responsible_cpf` + validação | Existe (unique + validação de dígitos) | ✅ | `app/models/family.py` + `_validate_cpf` em `app/main.py` |
| RG com validação/máscara | `families.responsible_rg` + regra formal | Campo existe, sem validação/máscara dedicada | ⚠️ | `app/models/family.py`, `templates/family_form.html` |
| Data nascimento + cálculo de idade | `families.birth_date` + idade computada | Campo existe; cálculo de idade existe utilitário, não persistido nem exibido como regra do cadastro | ⚠️ | `app/models/family.py`, `_calculate_age` em `app/main.py` |
| Endereço via CEP (Correios/equivalente) | CEP + integração | CEP existe e integração ViaCEP existe | ✅ | `app/models/family.py`, `/api/cep/{cep}` em `app/main.py`, `app/services/viacep_client.py` |
| Listas suspensas (estado civil, instrução, tipo moradia, doenças, benefícios) | colunas/enums específicos | Não encontrados como colunas dedicadas; apenas campos textuais genéricos (`socioeconomic_profile`, `documentation_status`) | ❌ | `app/models/family.py`, migração `0003_family_dependent.py` |
| Crianças dependentes (até 10) + nomes + parentesco | limite + estrutura explícita | Dependentes existem sem limite de 10; parentesco existe em `dependents.relationship`; crianças em tabela separada sem vínculo com “até 10 dependentes” | ⚠️ | `app/models/family.py` |
| Certidão nascimento (sim/não + faltantes) | campo boolean/lista | Não encontrado | ❌ | não há coluna específica em `app/models/family.py` |
| Parceiro(a) com validação de duplicidade | entidade/campo parceiro + regra | Não encontrado | ❌ | não há coluna/relacionamento dedicado |
| Contador adultos (até 12) e trabalhadores (até 10) | colunas/constraints | Não encontrado | ❌ | não há colunas específicas |
| Renda por trabalhador e renda total | estrutura renda individual + agregação | Dependente tem `income`; não há estrutura de “trabalhadores” nem cálculo/persistência de renda total familiar | ⚠️ | `app/models/family.py`, `dependents.income` |
| “Frequenta igreja?” | campo boolean/enum | Não encontrado | ❌ | ausência em `families` |
| “Necessita visita? (ALERTA)” | campo + gatilho de alerta | Não há campo explícito; existe módulo de solicitações de visita separado | ⚠️ | `VisitRequest` em `app/models/family.py` |

### Síntese — Famílias
A base cobre cadastro principal, CPF único e CEP, mas não implementa várias estruturas obrigatórias do PDF (listas fechadas, parceiro, contadores, certidão, frequência à igreja). O modelo atual usa campos textuais amplos em vez de schema estrito.

## 2) Cestas Básicas (PDF pág. 2)

| Requisito (PDF) | Esperado | Encontrado | Status | Evidência |
|---|---|---|---|---|
| ID_Cesta + FK família | PK + FK | Existe (`food_baskets.id`, `family_id`) | ✅ | `app/models/family.py`, `0005_food_baskets.py` |
| Data de entrega automática | coluna data explícita | Não existe coluna de data da entrega; existe `created_at` e referência mês/ano | ❌ | `FoodBasket` em `app/models/family.py` |
| Quantidade (padrão 1) | `quantity` default 1 | Não existe | ❌ | ausência em `FoodBasket` |
| Frequência mensal configurável | regra/config por família/sistema | Não encontrado no modelo de cestas | ❌ | ausência em `FoodBasket` |
| Última retirada (data + nome responsável) | colunas dedicadas | Não encontrado | ❌ | ausência em `FoodBasket` |
| Status família (Apta/Já beneficiada/Atenção) | enum com esses estados | Enum atual é Entregue/Pendente/Cancelada | ❌ | `FoodBasketStatus` em `app/models/family.py` |
| Observações | `notes` | Existe | ✅ | `FoodBasket.notes` |

### Síntese — Cestas
Implementação atual diverge da tabela solicitada: modelo por competência mensal e status operacional interno, sem os campos de operação social descritos no PDF.

## 3) Equipamentos e Empréstimos (PDF pág. 2–3)

| Requisito (PDF) | Esperado | Encontrado | Status | Evidência |
|---|---|---|---|---|
| Tipo equipamento (bengala/cadeira/...) | enum/tipo | Não há enum de tipo; existe `description` livre | ❌ | `app/models/equipment.py` |
| Estado conservação (novo/bom/reparo) | enum estado físico | Não existe; há status disponibilidade | ❌ | `Equipment.status` |
| Observações do equipamento | campo notes | Não existe no equipamento (apenas em empréstimo) | ❌ | `Equipment` |
| Empréstimo FK família + FK equipamento | FKs obrigatórias | Existe | ✅ | `Loan.family_id`, `Loan.equipment_id` |
| Retirada automática | data automática | `loan_date` é informada no formulário, não automática | ⚠️ | `create_loan` em `app/main.py` |
| Devolução automática | data automática | `returned_at` definida no retorno (automática no ato de devolução), mas não há previsão automática de data inicial | ⚠️ | `return_loan` |
| Prazo devolução obrigatório | `due_date` obrigatório | Campo existe, mas opcional (`nullable=True`) | ❌ | `Loan.due_date` |
| Estado na devolução (bom/manutenção) | campo de inspeção | Não existe | ❌ | ausência em `Loan` |
| Status equipamento disponível/emprestado/manutenção | enum com manutenção | Enum atual: Disponível/Emprestado/Indisponível (sem manutenção explícita) | ⚠️ | `EquipmentStatus` |
| Alertas prazo vencido em vermelho | regra + UI | Há destaque de atraso na UI de detalhe, mas sem campo de manutenção/devolução completo | ⚠️ | `templates/equipment_detail.html` |
| Histórico de uso | lista de empréstimos | Existe | ✅ | relacionamento `Equipment.loans` |

## 4) Moradores de Rua (PDF pág. 3–4)

| Requisito (PDF) | Esperado | Encontrado | Status | Evidência |
|---|---|---|---|---|
| Documentos (sim/não/parcial) | enum/campo estruturado | Não há enum dedicado; há CPF/RG livres e notas | ❌ | `app/models/street.py` |
| Tempo em situação de rua (faixas) | enum de faixas | Não encontrado | ❌ | ausência em `StreetPerson` |
| Necessidades imediatas (multi seleção) | campo multivalor | Não encontrado | ❌ | ausência em `StreetPerson` |
| Acompanhamento espiritual (oração/visita com alerta) | campos + alerta | Não encontrado | ❌ | ausência em `StreetPerson`/rotas |
| Decisão espiritual (reconciliação/conversão/...) | enum/campo | Não encontrado | ❌ | ausência em `StreetPerson` |
| Encaminhamentos CRAS/CAPS/UBS/Documentos/Trabalho/Outro | enum/taxonomia | Existe módulo de encaminhamento, mas campo é texto livre `recovery_home`; sem taxonomia fixa | ⚠️ | `Referral.recovery_home` |
| Termo de consentimento (registro + assinatura + data) | consentimento + assinatura + data | Consentimento e data existem; assinatura nominal não existe como campo específico | ⚠️ | `StreetPerson.consent_*` |

## 5) Diferenças e correções sugeridas (DB/migrations)

## P0 (bloqueia aderência principal ao PDF)
1. **Redesenhar schema de Famílias para os campos obrigatórios do PDF**  
   - Novas colunas/enums: estado civil, instrução, tipo de moradia, doenças crônicas, benefícios, frequenta igreja, necessita visita (alerta), parceiro(a), certidão.  
   - Tabela filha para trabalhadores/renda e limites de domínio.
2. **Evoluir `food_baskets` para o modelo da tabela de Cestas do PDF**  
   - `delivery_date`, `quantity default 1`, `frequency_months`, `last_withdrawal_at`, `last_withdrawal_responsible`, `family_status` enum.
3. **Incluir campos mandatórios de rua**  
   - documentos_status enum, tempo_rua enum, necessidades_imediatas (join table), acompanhamento/decisão espiritual, consent_signature_name.

## P1 (impacta operação)
1. **Equipamentos**: adicionar `equipment_type`, `condition_status`, `equipment_notes`.  
2. **Empréstimos**: `due_date` obrigatório, `return_condition`, `overdue_flag` derivável e índice de pendência.

## P2 (melhoria/qualidade)
1. Catalogar enums em tabelas parametrizáveis (evitar texto livre).  
2. Adicionar constraints de limite de quantidade (ex.: dependentes/trabalhadores) via regra de aplicação + validação de banco quando possível.

## Migrações necessárias (sugestão de ordem)
1. `xxxx_pdf_families_required_fields.py`  
2. `xxxx_pdf_food_basket_redesign.py`  
3. `xxxx_pdf_equipment_condition_and_type.py`  
4. `xxxx_pdf_street_required_fields.py`  
5. `xxxx_pdf_indexes_and_constraints.py`

Cada migration deve conter estratégia de **backfill** para dados existentes e default seguro para ambiente em produção.
