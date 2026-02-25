# ADR-0002 — Conflito de Fonte de Verdade (DOCX oficial vs PDF em DB_RULES)

- Status: Proposto
- Data: 2026-02-25

## Contexto
Durante a auditoria final foi identificado conflito normativo:
- A instrução de auditoria define `Especificacao_Sistema_Igreja_Social_PHP_MySQL.docx` como **fonte de verdade final**.
- `docs/DB_RULES_MYSQL.md` define o PDF `VersaoFinalSistemaWeb_Pib2026 (1).pdf` como **fonte de verdade única** para schema.

Esse conflito impacta diretamente decisões de modelagem, rastreabilidade e aceite de mudanças.

## Opções avaliadas

### Opção A — Manter PDF como fonte única para banco e DOCX para restante
- Prós: preserva histórico atual de DB rules.
- Contras: cria dupla governança e divergência permanente.

### Opção B — Promover DOCX como fonte única institucional (incluindo DB) e tratar PDF como referência histórica
- Prós: unifica governança, reduz ambiguidade de implementação.
- Contras: exige atualização de `DB_RULES_MYSQL.md` e possível remapeamento de alguns campos.

## Decisão proposta
Adotar **Opção B**: usar o DOCX como fonte de verdade oficial final para todo o sistema e rebaixar o PDF para referência histórica/comparativa.

## Consequências
1. Atualizar `docs/DB_RULES_MYSQL.md` para remover “fonte única PDF”.
2. Manter seção de compatibilidade histórica com PDF para rastreabilidade.
3. Exigir que novos requisitos/alterações referenciem o DOCX oficial (e seção/página/linha correspondente).

## Plano de execução sugerido
1. Aprovação deste ADR pela governança técnica/negócio.
2. Revisão documental (DB rules + checklist de PR).
3. Revisão incremental de migrations para alinhamento formal ao DOCX.

