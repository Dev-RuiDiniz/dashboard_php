# Relatório pós-correções de aderência

## Resumo
Este ciclo implementou correções estruturais no **schema**, **backend** e **frontend** com base nos gaps apontados na auditoria anterior.

## Correções implementadas

### Banco de dados e modelos
- Inclusão de campos de famílias para parceiro(a), estado civil, instrução, moradia, doenças crônicas, benefícios, frequência à igreja, alerta de visita, certidão de nascimento, contadores e renda total.
- Inclusão de tabela `family_workers` para renda por trabalhador.
- Evolução de `food_baskets` com `delivery_date`, `quantity`, `frequency_months`, `last_withdrawal_at`, `last_withdrawal_responsible` e `family_status` (Apta/Já beneficiada/Atenção).
- Evolução de equipamentos com `equipment_type`, `condition_status` e `notes`.
- Evolução de empréstimos com `return_condition` e validação de prazo obrigatório em backend.
- Evolução de moradores de rua com `documents_status`, `street_time`, `immediate_needs`, acompanhamento espiritual, decisão espiritual e assinatura de consentimento.
- Evolução de encaminhamentos com `target` (CRAS/CAPS/UBS/Documentos/Trabalho/Outro).
- Nova migration: `0016_pdf_aderencia_campos_regras.py`.

### Backend
- Atualização de criação de família para validar limites e capturar novos campos.
- Cálculo automático de renda total via trabalhadores + dependentes (`_recalculate_family_income`).
- Limite de até 10 dependentes na inclusão.
- Equipamentos: criação/edição com tipo/condição/observações.
- Empréstimos: prazo de devolução obrigatório e validação de data.
- Devolução: captura condição de devolução e envio para manutenção quando necessário.
- Rua: criação com novos campos e assinatura de consentimento.
- Encaminhamento: captura de destino oficial (`target`).

### Frontend
- Formulário de família ampliado com novos campos e entrada de trabalhadores (Nome;Renda).
- Formulário de equipamento ampliado (tipo, conservação, observações).
- Formulário de empréstimo atualizado para prazo obrigatório.
- Detalhe de equipamento atualizado com condição na devolução e campos adicionais.
- Formulário de pessoa em situação de rua ampliado com documentação, tempo de rua, necessidades imediatas, acompanhamento/decisão espiritual e assinatura de consentimento.
- Detalhe de pessoa em situação de rua com exibição dos novos campos.

## Evidência visual
- Screenshot da tela de família com novos campos:
  - ![Tela de família com novos campos](browser:/tmp/codex_browser_invocations/dcde4bbff20e4be1/artifacts/artifacts/family_form_new_fields.png)

## Situação atual
- Aderência avançou de forma relevante nos módulos críticos (Famílias, Cestas, Equipamentos/Empréstimos, Rua).
- Ainda há necessidade de rodada adicional para harmonizar 100% dos detalhes em todos os fluxos de edição/listagem e cobertura de testes automatizados de regressão dos novos campos.
