# Constituição do Banco MySQL (Projeto PIB 2026)

## 1. Propósito e Fonte de Verdade

Este documento define regras **obrigatórias** para modelagem, integridade, índices, constraints, auditoria e migrações do banco MySQL do projeto.

**Fonte de verdade única:** PDF `VersaoFinalSistemaWeb_Pib2026 (1).pdf` (arquivo de referência em `/mnt/data/VersaoFinalSistemaWeb_Pib2026 (1).pdf`, disponível neste repositório como `./VersaoFinalSistemaWeb_Pib2026 (1).pdf`).

> Regra mandatória: qualquer mudança de schema deve ser rastreável aos campos/tabelas do PDF. Se algo não estiver explícito no PDF, registrar como **NÃO DEFINIDO NO PDF** e tratar como decisão técnica (sem inventar requisito funcional).

---

## 2. Regras Inquebráveis (Do/Don’t)

### DO
- Usar somente entidades/campos que tenham origem no PDF.
- Nomear tabelas/colunas em `snake_case`.
- Definir PK, FK, `UNIQUE` e índices de busca para campos operacionais (CPF, nomes, status, datas).
- Modelar campos de **lista múltipla** como relacionamento **N:N** com tabela associativa.
- Tratar campos de **texto com máscara** como `VARCHAR`, com máscara/validação no app e constraint no banco quando viável (ex.: unicidade de CPF).
- Registrar claramente no PR quando algo for **decisão técnica** por ausência de definição no PDF.

### DON’T
- Não criar tabela/campo “genérico” (ex.: `dados`, `extra_json`) para acomodar requisitos não mapeados.
- Não duplicar CPF para a mesma pessoa no escopo da mesma entidade sem justificativa formal.
- Não remover constraints/FKs sem migração explícita e justificativa técnica.
- Não criar gatilhos de regra de negócio não descrita no PDF.

### Decisões técnicas (não funcionais) permitidas
- `soft delete`, trilha de auditoria detalhada, e timestamps automáticos (`created_at`/`updated_at`) são decisões técnicas permitidas por governança, mas **NÃO DEFINIDOS NO PDF**.

---

## 3. Convenções e Padrões de Schema

- **SGBD alvo:** MySQL 8.0+
- **Engine:** InnoDB
- **Charset/Collation:** `utf8mb4` / `utf8mb4_0900_ai_ci`
- **Naming:**
  - tabelas em plural (`families`, `basic_baskets`, `equipments`, `equipment_loans`, `street_residents`)
  - colunas em `snake_case`
  - chaves estrangeiras com prefixo `id_` no conceito e implementação com sufixo `_id` (ex.: `family_id`)
  - índices: `idx_<table>_<colunas>`
  - uniques: `uq_<table>_<colunas>`
  - FKs: `fk_<origem>_<destino>`
- **PK padrão (decisão técnica):** `BIGINT UNSIGNED AUTO_INCREMENT`.
- **Timestamps (`created_at`, `updated_at`):** decisão técnica recomendada; **NÃO DEFINIDO NO PDF**.
- **Auditoria de alteração (`created_by`, `updated_by`, trilha):** decisão técnica recomendada; **NÃO DEFINIDO NO PDF**.
- **Soft delete (`deleted_at`):** opcional; **NÃO DEFINIDO NO PDF**.

---

## 4. Modelagem Derivada do PDF (Tabelas Oficiais)

## 4.1 `families`
**Finalidade:** cadastro socioassistencial de famílias e responsável.

| coluna | tipo mysql | null | default | regra/validação | origem no PDF (campo) |
|---|---|---|---|---|---|
| id | BIGINT UNSIGNED | não | auto_increment | PK | `ID_Família (PK)` |
| responsible_full_name | VARCHAR(150) | não | — | obrigatório; deduplicação por regra de negócio | `Nome completo do(a) Responsável` |
| responsible_cpf | VARCHAR(14) | não | — | máscara CPF; validação app; único | `CPF` |
| responsible_rg | VARCHAR(20) | sim | NULL | máscara RG; validação app | `RG` |
| birth_date | DATE | sim | NULL | idade calculada no app/view | `Data de nascimento` |
| birth_place | VARCHAR(120) | sim | NULL | texto livre | `Naturalidade` |
| phone | VARCHAR(20) | sim | NULL | máscara telefone | `Telefone` |
| marital_status_code | VARCHAR(40) | sim | NULL | FK lookup | `Estado civil` |
| professional_status_code | VARCHAR(40) | sim | NULL | FK lookup | `Situação Profissional` |
| professional_status_other | VARCHAR(120) | sim | NULL | obrigatório quando “autônomo/outro” | `Trabalhando autônomo: Qual tipo de ocupação?` |
| education_level_code | VARCHAR(40) | sim | NULL | FK lookup | `Grau de instrução` |
| cep | VARCHAR(9) | sim | NULL | máscara CEP | `Endereço (CEP + texto)` |
| address_text | VARCHAR(255) | sim | NULL | endereço textual | `Endereço (CEP + texto)` |
| location_reference | VARCHAR(255) | sim | NULL | texto livre | `Referência de localização` |
| housing_type_code | VARCHAR(50) | sim | NULL | FK lookup | `Tipo de moradia` |
| chronic_disease_code | VARCHAR(50) | sim | NULL | FK lookup (lista do PDF) | `Possui alguma Doença Crônica?` |
| has_physical_disability | TINYINT(1) | não | 0 | 0/1 | `Possui alguma Deficiência Física?` |
| physical_disability_description | VARCHAR(255) | sim | NULL | preencher quando = sim | `Sim: Qual? Texto Livre` |
| continuous_medication_use | TINYINT(1) | não | 0 | 0/1 | `Faz Uso de Medicação Contínua?` |
| continuous_medication_description | VARCHAR(255) | sim | NULL | preencher quando = sim | `Sim: Qual(is)? Texto Livre` |
| social_benefit_code | VARCHAR(60) | sim | NULL | FK lookup | `Recebe Benefício social?` |
| dependent_children_count | TINYINT UNSIGNED | sim | NULL | 0..10 | `Nº de crianças dependentes?` |
| partner_full_name | VARCHAR(150) | sim | NULL | deduplicação app | `Parceiro(a) Nome completo` |
| partner_cpf | VARCHAR(14) | sim | NULL | máscara CPF; único quando informado | `CPF` (parceiro) |
| partner_rg | VARCHAR(20) | sim | NULL | máscara RG | `RG` (parceiro) |
| partner_phone | VARCHAR(20) | sim | NULL | máscara telefone | `Telefone` (parceiro) |
| total_adults_count | TINYINT UNSIGNED | sim | NULL | 0..12 | `Nº total de adultos residindo no mesmo endereço?` |
| total_workers_count | TINYINT UNSIGNED | sim | NULL | 0..10 | `Nº de trabalhadores no mesmo endereço` |
| income_per_worker | DECIMAL(10,2) | sim | NULL | moeda | `Renda por trabalhador` |
| total_income | DECIMAL(10,2) | sim | NULL | cálculo automático (app ou coluna gerada) | `Cálculo automático da renda total` |
| attends_church | TINYINT(1) | não | 0 | 0/1 | `Frequenta alguma igreja?` |
| church_name | VARCHAR(150) | sim | NULL | quando = sim | `Sim: Qual? Texto Livre` |
| general_notes | TEXT | sim | NULL | texto livre | `Observações gerais` |
| needs_visit | TINYINT(1) | não | 0 | alerta quando sim | `Necessita Visita?` |

**Constraints**
- `PRIMARY KEY (id)`.
- `UNIQUE (responsible_cpf)`.
- `UNIQUE (partner_cpf)` com semântica “NULLs permitidos”.
- `CHECK` (ou validação app) para faixas: `dependent_children_count <= 10`, `total_adults_count <= 12`, `total_workers_count <= 10`.

**Índices**
- `idx_families_responsible_name` (`responsible_full_name`).
- `idx_families_responsible_cpf` (`responsible_cpf`).
- `idx_families_status_visit` (`needs_visit`).
- `idx_families_marital_professional` (`marital_status_code`, `professional_status_code`).

**Relacionamentos (FKs)**
- lookups: estado civil, situação profissional, instrução, moradia, doença crônica, benefício social.

**Observações**
- “Nome de cada criança + parentesco” vira tabela filha (1:N) com parentesco em lookup.
- “Apresentação da certidão de nascimento” vira estrutura documental por criança (1:N).

### Tabelas associadas de `families` (derivadas do PDF)

#### 4.1.1 `family_children`
| coluna | tipo mysql | null | default | regra/validação | origem no PDF (campo) |
|---|---|---|---|---|---|
| id | BIGINT UNSIGNED | não | auto_increment | PK | derivado técnico |
| family_id | BIGINT UNSIGNED | não | — | FK obrigatória | `ID_Família (FK implícita)` |
| child_name | VARCHAR(150) | não | — | texto livre | `Nome de cada criança` |
| kinship_code | VARCHAR(40) | não | — | FK lookup parentesco | `Parentesco: Filho/Neto/Bisneto/Sobrinho/Enteado/Adotado` |

#### 4.1.2 `family_child_documents`
| coluna | tipo mysql | null | default | regra/validação | origem no PDF (campo) |
|---|---|---|---|---|---|
| id | BIGINT UNSIGNED | não | auto_increment | PK | derivado técnico |
| family_child_id | BIGINT UNSIGNED | não | — | FK obrigatória | `Nome de cada criança` |
| birth_certificate_presented | TINYINT(1) | não | 0 | 0/1 | `Apresentação da certidão de Nascimento (Sim/Não)` |
| missing_birth_certificate_note | VARCHAR(255) | sim | NULL | obrigatório quando não apresentado | `Indicar quais certidões... faltando` |

---

## 4.2 `basic_baskets`
**Finalidade:** controle de entregas de cestas básicas por família.

| coluna | tipo mysql | null | default | regra/validação | origem no PDF (campo) |
|---|---|---|---|---|---|
| id | BIGINT UNSIGNED | não | auto_increment | PK | `ID_Cesta (PK)` |
| family_id | BIGINT UNSIGNED | não | — | FK obrigatória | `ID_Família (FK)` |
| delivery_date | DATE | não | CURRENT_DATE | registro automático da data | `Data da entrega` |
| quantity | SMALLINT UNSIGNED | não | 1 | padrão 1; permite ajuste | `Quantidade de cestas` |
| frequency | VARCHAR(30) | não | 'mensal' | mensal configurável | `Frequência` |
| last_withdrawal_info | VARCHAR(255) | sim | NULL | data + responsável | `Última retirada` |
| family_status_code | VARCHAR(30) | sim | NULL | lookup/enum | `Status da família` |
| notes | TEXT | sim | NULL | texto livre | `Observações` |

**Constraints**
- `PRIMARY KEY (id)`.
- `FOREIGN KEY (family_id)`.
- `CHECK (quantity >= 1)`.

**Índices**
- `idx_baskets_family_date` (`family_id`, `delivery_date`).
- `idx_baskets_family_status` (`family_status_code`).

**Relacionamentos (FKs)**
- `basic_baskets.family_id -> families.id`.

**Observações**
- Regra “bloquear múltiplas entregas no mês” = **NÃO DEFINIDO NO PDF** como bloqueio rígido; implementar no app se desejado.

---

## 4.3 `equipments`
**Finalidade:** cadastro de equipamentos assistivos.

| coluna | tipo mysql | null | default | regra/validação | origem no PDF (campo) |
|---|---|---|---|---|---|
| id | BIGINT UNSIGNED | não | auto_increment | PK | `ID_Equipamento (PK)` |
| equipment_name_code | VARCHAR(40) | não | — | lookup (bengala, cadeira etc.) | `Nome do equipamento` |
| conservation_state_code | VARCHAR(30) | não | — | novo/bom/precisa reparo | `Estado de conservação` |
| notes | TEXT | sim | NULL | detalhes livres | `Observações` |
| equipment_status_code | VARCHAR(30) | não | 'disponivel' | disponível/emprestado/manutenção | `Status do equipamento` |

**Constraints**
- `PRIMARY KEY (id)`.
- `CHECK` em status/conservação (ou lookup com FK).

**Índices**
- `idx_equipments_name` (`equipment_name_code`).
- `idx_equipments_status` (`equipment_status_code`).
- `idx_equipments_conservation` (`conservation_state_code`).

**Relacionamentos (FKs)**
- FKs para lookups de tipo, conservação e status.

---

## 4.4 `equipment_loans`
**Finalidade:** registrar empréstimos, devoluções e histórico de uso dos equipamentos.

| coluna | tipo mysql | null | default | regra/validação | origem no PDF (campo) |
|---|---|---|---|---|---|
| id | BIGINT UNSIGNED | não | auto_increment | PK | `ID_Empréstimo (PK)` |
| family_id | BIGINT UNSIGNED | não | — | FK obrigatória | `ID_Família (FK)` |
| equipment_id | BIGINT UNSIGNED | não | — | FK obrigatória | `ID_Equipamento (FK)` |
| withdrawal_date | DATE | não | CURRENT_DATE | registro automático | `Data de retirada` |
| return_deadline | DATE | não | — | obrigatório | `Prazo de devolução` |
| return_date | DATE | sim | NULL | automático na devolução | `Data de devolução` |
| return_conservation_state_code | VARCHAR(30) | sim | NULL | bom/precisa manutenção | `Estado do equipamento na devolução` |
| notes | TEXT | sim | NULL | texto livre | `Observações` |

**Constraints**
- `PRIMARY KEY (id)`.
- `FOREIGN KEY (family_id)`.
- `FOREIGN KEY (equipment_id)`.
- `CHECK (return_date IS NULL OR return_date >= withdrawal_date)`.

**Índices**
- `idx_loans_equipment_open` (`equipment_id`, `return_date`).
- `idx_loans_family_date` (`family_id`, `withdrawal_date`).
- `idx_loans_deadline` (`return_deadline`).

**Relacionamentos (FKs)**
- `equipment_loans.family_id -> families.id`.
- `equipment_loans.equipment_id -> equipments.id`.

**Observações**
- “Alertas de devolução vencida”, “documentação pendente” e “histórico de uso” são suportados por consultas/visões; regras detalhadas de SLA não estão formalizadas no PDF.

---

## 4.5 `street_residents`
**Finalidade:** cadastro e acompanhamento de pessoas em situação de rua.

| coluna | tipo mysql | null | default | regra/validação | origem no PDF (campo) |
|---|---|---|---|---|---|
| id | BIGINT UNSIGNED | não | auto_increment | PK | `ID_Morador (PK)` |
| full_name | VARCHAR(150) | não | — | registro básico | `Nome completo` |
| social_name | VARCHAR(150) | sim | NULL | registro básico | `Nome social` |
| birth_date | DATE | sim | NULL | idade calculada no app | `Data de nascimento / Idade` |
| cpf | VARCHAR(14) | sim | NULL | máscara/validação app | `CPF (se tiver)` |
| rg | VARCHAR(20) | sim | NULL | máscara/validação app | `RG (se tiver)` |
| birth_place | VARCHAR(120) | sim | NULL | texto | `Naturalidade` |
| marital_status_code | VARCHAR(40) | sim | NULL | FK lookup | `Estado Civil` |
| document_status_code | VARCHAR(20) | sim | NULL | sim/não/parcialmente | `Possui documentos?` |
| usual_location | VARCHAR(255) | sim | NULL | texto livre | `Local onde costuma permanecer` |
| street_time_code | VARCHAR(40) | sim | NULL | FK lookup | `Quanto tempo em situação de rua?` |
| has_family_in_region | TINYINT(1) | não | 0 | 0/1 | `Possui família em Taubaté, na região?` |
| family_contact | VARCHAR(150) | sim | NULL | quando = sim | `Sim: contato` |
| has_chronic_disease | TINYINT(1) | não | 0 | 0/1 | `Sofre de Doença crônica?` |
| chronic_disease_description | VARCHAR(255) | sim | NULL | quando = sim | `Sim: Qual? Texto Livre` |
| uses_continuous_medication | TINYINT(1) | não | 0 | 0/1 | `Faz uso de Medicação Contínua?` |
| continuous_medication_description | VARCHAR(255) | sim | NULL | quando = sim | `Sim: Qual? Texto Livre` |
| uses_alcohol_or_drugs | TINYINT(1) | não | 0 | 0/1 | `Faz Uso de álcool/outras substâncias?` |
| alcohol_drug_notes | VARCHAR(255) | sim | NULL | observações | `Sim: Observações` |
| disability_type_code | VARCHAR(40) | sim | NULL | FK lookup | `Possui deficiência?` |
| education_level_code | VARCHAR(40) | sim | NULL | FK lookup | `Escolaridade` |
| profession_skills | VARCHAR(255) | sim | NULL | texto livre | `Profissão / Habilidades` |
| has_formal_work_history | TINYINT(1) | sim | NULL | sim/não | `Já trabalhou com carteira assinada?` |
| is_interested_in_work | TINYINT(1) | sim | NULL | sim/não | `Interesse em trabalho` |
| work_interest_description | VARCHAR(255) | sim | NULL | quando = sim | `Sim: Qual? Texto Livre` |
| other_immediate_needs | VARCHAR(255) | sim | NULL | texto livre | `Outras Necessidades?` |
| attends_church | TINYINT(1) | não | 0 | 0/1 | `Frequenta Alguma Igreja?` |
| church_name | VARCHAR(150) | sim | NULL | quando = sim | `Sim: Qual? (Texto)` |
| notes | TEXT | sim | NULL | texto livre | `Observações` |
| consent_text_accepted | TINYINT(1) | não | 0 | aceite do termo | `Termo de consentimento` |
| consent_signature | VARCHAR(150) | sim | NULL | assinatura | `Assinatura + data` |
| consent_date | DATE | sim | NULL | data do consentimento | `Assinatura + data` |

**Constraints**
- `PRIMARY KEY (id)`.
- `UNIQUE (cpf)` opcional (pode ser parcial/condicional por ausência frequente de documento; decisão técnica).
- Checks condicionais para campos “quando sim”.

**Índices**
- `idx_street_residents_name` (`full_name`).
- `idx_street_residents_cpf` (`cpf`).
- `idx_street_residents_location` (`usual_location`).
- `idx_street_residents_street_time` (`street_time_code`).

**Relacionamentos (FKs)**
- lookups de estado civil, tempo de rua, deficiência, escolaridade, status documental.

### 4.5.1 N:N obrigatórias de `street_residents` (listas múltiplas)

#### a) `street_resident_immediate_needs` (N:N)
- Liga morador em situação de rua às necessidades imediatas.
- Origem: `Necessidades imediatas` (lista múltipla).

#### b) `street_resident_spiritual_followups` (N:N)
- Liga morador aos itens de acompanhamento espiritual.
- Origem: `Acompanhamento espiritual` (lista múltipla; inclui oração/visita).

#### c) `street_resident_spiritual_decisions` (N:N)
- Liga morador às decisões espirituais.
- Origem: `Decisão espiritual` (lista múltipla).

#### d) `street_resident_referrals` (N:N)
- Liga morador aos encaminhamentos realizados.
- Origem: `Encaminhamentos realizados` (lista múltipla).

---

## 5. Campos de “Lista Suspensa” e Valores Permitidos

> Critério técnico de modelagem:
> - **ENUM**: listas pequenas e estritamente estáveis.
> - **Lookup table**: listas que podem crescer, mudar nomenclatura ou exigir gestão.
> - Como o PDF não define “configurável”, quando houver dúvida optar por **lookup table** (decisão técnica de governança).

| item do PDF | valores do PDF | modelagem | observação |
|---|---|---|---|
| Estado civil | Solteiro(a), Casado(a), Divorciado(a), Viúvo(a), União estável | Lookup table `lk_marital_status` | reaproveitado em famílias e rua |
| Situação profissional | Empregado, Desempregado, Autônomo (+ texto livre) | Lookup `lk_professional_status` + campo `*_other` | precisa suportar complemento |
| Grau de instrução / Escolaridade | alfabetização funcional, analfabeto, fundamental, médio, superior; não alfabetizado | Lookup `lk_education_level` | normalizar variação textual |
| Tipo de moradia | própria, MCMV, alugada, cedida, ocupação irregular | Lookup `lk_housing_type` | domínio social pode crescer |
| Doença crônica (famílias) | hipertensão, diabetes, cardiovasculares, obesidade, osteomuscular, depressão/transtornos mentais | Lookup `lk_chronic_disease` | permite evolução futura |
| Benefício social | bolsa família, BPC/LOAS, tarifa social energia, aposentadoria | Lookup `lk_social_benefit` | pode crescer |
| Tempo em situação de rua | menos de 3 meses, 3-12 meses, 1-5 anos, +5 anos | **ENUM** (ou lookup) | fechado e pequeno |
| Necessidades imediatas | alimentação, higiene, roupas, documentação, atendimento médico, acolhimento/abrigo, apoio psicológico, tratamento dependência química, orientação espiritual | Lookup + N:N | lista múltipla obrigatória |
| Encaminhamentos realizados | CRAS, CAPS, albergue, UBS, documentos, trabalho, outro | Lookup + N:N | lista múltipla obrigatória |
| Acompanhamento espiritual | deseja oração, aceita visita | Lookup + N:N | lista múltipla |
| Decisão espiritual | reconciliação, conversão, interesse, apoio social | Lookup + N:N | lista múltipla |
| Estado de conservação (equipamento) | novo, bom, precisa reparo | **ENUM** | fechado e operacional |
| Estado na devolução | bom, precisa manutenção | **ENUM** | fechado e operacional |
| Status do equipamento | disponível, emprestado, manutenção | **ENUM** | fechado e operacional |
| Status da família | apta, já beneficiada (no mês/anterior), atenção | Lookup `lk_family_status` | texto do PDF tem variação por contexto |
| Deficiência (rua) | física, intelectual, visual, auditiva, não possui | Lookup `lk_disability_type` | domínio com tendência de ajuste |
| Possui documentos? | sim, não, parcialmente | **ENUM** | fechado e pequeno |

---

## 6. Regras de Integridade e Regras de Negócio no Banco

Aplicar no banco **somente** o que o PDF suporta explicitamente:

1. **Unicidade de CPF**
   - Responsável da família: obrigatório e único.
   - Parceiro(a): único quando informado.
   - Morador de rua: **NÃO DEFINIDO NO PDF** como obrigatório; tratar como opcional.

2. **Faixas numéricas explícitas**
   - Crianças dependentes até 10.
   - Adultos no endereço até 12.
   - Trabalhadores no endereço até 10.

3. **Datas de empréstimo/devolução**
   - Prazo de devolução obrigatório.
   - Devolução não pode ser anterior à retirada.

4. **Listas múltiplas**
   - Sempre em N:N (sem armazenar CSV/JSON em coluna de texto).

5. **Regras não explicitadas no PDF**
   - Ex.: bloqueio rígido de múltiplas cestas/mês, SLA de alertas, workflow de aprovação.
   - Status: **NÃO DEFINIDO NO PDF** → implementar no app e/ou política operacional, sem trigger obrigatório no banco.

---

## 7. Estratégia de Migrações e Versionamento

**Ferramenta recomendada (decisão técnica): Flyway**
- Justificativa: versionamento SQL simples, histórico imutável, amplamente suportado com MySQL e pipelines CI.

### Política de migração
- Migrations são **imutáveis** após merge.
- Novo ajuste = nova migration incremental.
- Rollback por migration reversa (`undo` lógico) quando aplicável.
- Seeds de lookups em migration versionada e idempotente.
- Toda migration de schema deve atualizar este documento quando afetar regra.

### Convenção
- `V<yyyyMMddHHmm>__descricao_curta.sql`
- Separar `schema`, `lookup_seed`, `backfill` quando necessário.

---

## 8. Checklist de Conformidade (pré-PR)

- [ ] Mudou schema? Criou migration correspondente?
- [ ] Campo/tabela tem origem explícita no PDF?
- [ ] Algum item está marcado como **NÃO DEFINIDO NO PDF** quando aplicável?
- [ ] Listas múltiplas foram modeladas em N:N?
- [ ] Campos com máscara (CPF/RG/telefone/CEP) estão em `VARCHAR` + validação no app?
- [ ] Há `UNIQUE` para CPF conforme regra da entidade?
- [ ] FKs e ações `ON DELETE/ON UPDATE` foram definidas conscientemente?
- [ ] Índices cobrem filtros operacionais (nome, CPF, status, datas)?
- [ ] Não foi criado campo/tabela inventado sem marcação de decisão técnica?

---

## Exemplo (não-fonte-de-verdade)

```text
Exemplo apenas ilustrativo:
- family_id em basic_baskets com índice composto (family_id, delivery_date)
- tabela associativa street_resident_referrals para lista múltipla de encaminhamentos
```

---

## Auto-checagem

- Usei SOMENTE o PDF como base? **sim**
- Inventei alguma tabela/campo? **não** (somente tabelas técnicas derivadas para representar relações e listas múltiplas do próprio PDF)
- Mapeei listas múltiplas para N:N? **sim**
