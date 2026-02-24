# Auditoria de aderência — Frontend (telas + validações UI)

## Premissas
- Frontend atual é SSR (Jinja2), com formulários HTML postando diretamente para endpoints FastAPI.
- Evidência baseada em templates e handlers de `app/main.py`.

## 1) Famílias

| Campo/regra no PDF | Existe na tela? | Validação UI? | Endpoint que salva | Status |
|---|---|---|---|---|
| Nome responsável | Sim | `required` | `POST /familias/nova` | ✅ |
| CPF com máscara | Parcial (campo existe, sem máscara visual nativa) | validação principal no backend | `POST /familias/nova` | ⚠️ |
| RG com máscara/validação | Parcial (campo texto livre) | não | `POST /familias/nova` | ⚠️ |
| Data nascimento + idade | Parcial (data existe, idade não exibida) | só tipo `date` | `POST /familias/nova` | ⚠️ |
| Endereço por CEP | Sim | botão “Buscar” + feedback | `GET /api/cep/{cep}` + `POST /familias/nova` | ✅ |
| Estado civil/instrução/moradia/doenças/benefícios (listas) | Não | — | — | ❌ |
| Crianças dependentes até 10 + parentesco | Parcial (dependentes e crianças existem, sem limite visual de 10) | validação de obrigatórios básicos | dependentes/crianças em rotas próprias | ⚠️ |
| Certidão nascimento (sim/não + faltantes) | Não | — | — | ❌ |
| Parceiro(a) com duplicidade | Não | — | — | ❌ |
| Contadores adultos/trabalhadores | Não | — | — | ❌ |
| Renda por trabalhador + total | Parcial (renda no dependente, sem total) | não | dependentes | ⚠️ |
| “Frequenta igreja?” | Não | — | — | ❌ |
| “Necessita visita? (ALERTA)” | Parcial (módulo de visitas existe, sem campo explícito no formulário principal) | alertas de pendência/atraso em tela de detalhe | visitas | ⚠️ |

## 2) Cestas básicas

| Campo/regra no PDF | Existe na tela? | Validação UI? | Endpoint | Status |
|---|---|---|---|---|
| ID_Cesta/FK família | Implícito (gerado no backend) | n/a | `POST /familias/{id}/cestas` | ✅ |
| Data da entrega automática | Não (tela pede mês/ano) | formato MM/AAAA | `POST /familias/{id}/cestas` | ❌ |
| Quantidade padrão 1 | Não | — | — | ❌ |
| Frequência mensal configurável | Não | — | — | ❌ |
| Última retirada data+responsável | Não | — | — | ❌ |
| Status Apta/Já beneficiada/Atenção | Não (status distintos) | seletor com enum atual | `POST /familias/{id}/cestas` | ❌ |
| Observações | Sim | textarea livre | `POST /familias/{id}/cestas` | ✅ |

## 3) Equipamentos e empréstimos

| Campo/regra no PDF | Existe na tela? | Validação UI? | Endpoint | Status |
|---|---|---|---|---|
| Tipo equipamento (lista fechada) | Não (descrição livre) | `required` só da descrição | `POST /equipamentos/novo` | ❌ |
| Estado conservação (novo/bom/reparo) | Não | — | — | ❌ |
| Observações de equipamento | Não | — | — | ❌ |
| Empréstimo com família/equipamento | Sim | família obrigatória | `POST /equipamentos/{id}/emprestimo` | ✅ |
| Data retirada automática | Parcial (campo manual) | `required` | `POST /equipamentos/{id}/emprestimo` | ⚠️ |
| Prazo devolução obrigatório | Não (opcional na UI) | opcional | `POST /equipamentos/{id}/emprestimo` | ❌ |
| Estado devolução (bom/manutenção) | Não | — | — | ❌ |
| Status disponível/emprestado/manutenção | Parcial (sem manutenção explícita) | seletor de status atual | `/equipamentos/*` | ⚠️ |
| Alerta vencido em vermelho | Parcial | destaque visual de atraso em detalhe | tela detalhe equipamento | ⚠️ |
| Histórico de uso | Sim | tabela/lista histórica | `GET /equipamentos/{id}` | ✅ |

## 4) Moradores de rua

| Campo/regra no PDF | Existe na tela? | Validação UI? | Endpoint | Status |
|---|---|---|---|---|
| Cadastro básico de identificação | Sim | obrigatórios mínimos | `POST /rua/nova` | ✅ |
| Documentos (sim/não/parcial) estruturado | Não | — | — | ❌ |
| Tempo em situação de rua (faixas) | Não | — | — | ❌ |
| Necessidades imediatas (multi seleção) | Não | — | — | ❌ |
| Acompanhamento espiritual (oração/visita + alerta) | Não | — | — | ❌ |
| Decisão espiritual (enum) | Não | — | — | ❌ |
| Encaminhamentos oficiais CRAS/CAPS/UBS/... | Parcial (texto livre) | obrigatórios básicos | `POST /rua/{id}/encaminhamentos` | ⚠️ |
| Consentimento com assinatura e data | Parcial | checkbox obrigatório (sem assinatura nominal) | `POST /rua/nova` | ⚠️ |

## 5) Prints / referências visuais
- Análise baseada em componentes de template:  
  - `templates/family_form.html`  
  - `templates/family_detail.html`  
  - `templates/equipment_form.html`  
  - `templates/loan_form.html`  
  - `templates/equipment_detail.html`  
  - `templates/street/street_person_form.html`  
  - `templates/street/street_person_detail.html`

> Nesta sprint não foi necessário gerar novos screenshots porque a entrega é de auditoria documental (sem alteração visual do produto).
