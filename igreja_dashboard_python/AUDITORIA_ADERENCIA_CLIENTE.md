# AUDITORIA DE ADERÊNCIA AO DOCUMENTO DO CLIENTE

Documento de referência funcional: **VersaoFinalSistemaWeb_Pib2026.pdf** (págs. 1–4, conforme escopo informado).  
Escopo auditado: banco de dados, backend e frontend para os módulos Famílias, Cestas, Equipamentos/Empréstimos e Moradores de Rua.

## 1) Resumo executivo

Status geral de aderência (estimado): **46%**.

- ✅ Há uma base funcional sólida (cadastros, validações de CPF, integração CEP, empréstimos, encaminhamentos, consentimento LGPD básico).
- ⚠️ Parte relevante está implementada de forma aproximada, mas com modelo de dados e fluxos diferentes do PDF.
- ❌ Há lacunas estruturais em campos obrigatórios e regras de negócio específicas do cliente.

Conclusão objetiva: **o sistema precisa de modificações para bater 1:1 com o documento do cliente**.

## 2) Principais riscos

1. **Risco de não conformidade funcional (P0)**: campos obrigatórios do PDF ausentes no schema/telas podem inviabilizar aceite formal.  
2. **Risco operacional (P1)**: regras de cestas e empréstimos não seguem exatamente o processo solicitado (status, prazo obrigatório, dados de retirada).  
3. **Risco de governança de dados (P1)**: uso de texto livre em pontos que deveriam ser enum/lista fechada dificulta padronização e indicadores.

## 3) Matriz de aderência por módulo

| Módulo | Aderência | Diagnóstico resumido |
|---|---:|---|
| Famílias | 50% | Base cadastral forte, porém sem várias colunas/regras mandatórias do PDF (listas fechadas, parceiro, certidão, contadores, frequenta igreja etc.). |
| Cestas | 30% | Existe controle mensal de cestas, mas modelo difere da tabela do cliente (faltam quantidade, frequência configurável, última retirada com responsável, status Apta/Já beneficiada/Atenção). |
| Equipamentos/Empréstimos | 52% | Fluxo operacional existe, porém faltam tipo/estado de conservação, manutenção explícita, prazo obrigatório e condição da devolução. |
| Moradores de Rua + Consentimento | 40% | Cadastro e encaminhamentos existem; faltam campos estruturados do PDF (tempo em rua, necessidades imediatas, decisões espirituais, assinatura de consentimento). |

## 4) Divergências por severidade

## P0 (bloqueia uso aderente ao contrato)
- Famílias sem campos mandatórios estruturados do PDF.  
- Cestas sem o contrato de dados esperado pela tabela do cliente.  
- Moradores de rua sem estrutura mínima exigida nas páginas 3–4.

## P1 (impacta operação)
- Empréstimos sem prazo obrigatório e sem estado na devolução.  
- Enumerações críticas modeladas como texto livre.

## P2 (melhoria/UX)
- Máscaras/validações de UI insuficientes para RG e campos específicos.  
- Trilha de auditoria “quem/quando” poderia cobrir 100% das operações CRUD de domínio.

## 5) O que está correto (✅)
- CPF com validação algorítmica e prevenção de duplicidade em famílias/dependentes/rua.  
- Integração de CEP com preenchimento de endereço.  
- Estrutura de empréstimos com histórico e controle de status básico.  
- Módulo de visitas e alertas de pendência/atraso.  
- Consentimento LGPD com termo ativo e registro de aceite/timestamp.

## 6) O que está parcial (⚠️)
- Cálculo de idade existe como utilitário, não como regra integral do fluxo solicitado.  
- Cestas e equipamentos existem, mas com semântica diferente da especificação do cliente.  
- Encaminhamentos de rua existem sem taxonomia fechada.  
- Trilha de auditoria existe, mas não está uniforme em todas as operações.

## 7) O que falta/diverge (❌)
- Campos específicos e listas fechadas de Famílias (págs. 1–2).  
- Contrato completo da tabela Cestas Básicas (pág. 2).  
- Campos de tipo/estado/condição de equipamentos e empréstimos (págs. 2–3).  
- Campos de rua e consentimento com assinatura nominal (págs. 3–4).

## 8) Mudanças recomendadas

## 8.1 DB (migrations)
1. Criar novas colunas/tabelas para atender integralmente o cadastro de famílias do PDF.  
2. Redesenhar `food_baskets` para o contrato do cliente.  
3. Evoluir `equipment`/`loans` com tipo, conservação, manutenção, condição de devolução e prazo obrigatório.  
4. Evoluir `street_people` com enums de documentos/tempo_rua/decisão espiritual e tabela de necessidades imediatas.  
5. Incluir estratégia de backfill e defaults seguros.

## 8.2 Backend (regras/endpoints)
1. Expor operações completas por módulo (CRUD real e regras automáticas conforme PDF).  
2. Implementar cálculo de status de cesta e alertas de forma determinística e auditável.  
3. Tornar validações de domínio explícitas (limites de dependentes/trabalhadores e campos obrigatórios específicos).

## 8.3 Frontend (campos/validações/alertas)
1. Atualizar formulários para todos os campos obrigatórios do cliente.  
2. Adicionar máscaras/validações de UI (RG, listas fechadas, multiseleção, limites).  
3. Ajustar estados visuais de alerta conforme nomenclatura contratual (ex.: ALERTA, vencido em vermelho, status oficiais).

## 9) Plano de correção (backlog sugerido)

1. **Sprint A (P0):** schema + API de Famílias/Cestas/Rua aderentes ao PDF.  
2. **Sprint B (P1):** equipamentos/empréstimos completos + taxonomias oficiais.  
3. **Sprint C (P2):** refinamentos de UX/validação, cobertura de auditoria total e homologação final.

Arquivos-alvo prováveis:
- `app/models/family.py`, `app/models/equipment.py`, `app/models/street.py`  
- `app/main.py`  
- `templates/family_*`, `templates/equipment_*`, `templates/street/*`  
- `alembic/versions/*` (novas revisões)

## 10) Definition of Done para encerrar aderência
- [ ] Todos os campos/regras das páginas 1–4 do PDF representados no schema e nas telas.  
- [ ] Endpoints e validações de backend cobrindo 100% dos requisitos funcionais.  
- [ ] Cada divergência com evidência técnica e validação de negócio homologada com o cliente.  
- [ ] Relatórios de auditoria atualizados sem itens P0 pendentes.

---

## Anexos desta sprint
- `docs/auditoria/inventario-sistema.md`
- `docs/auditoria/01-db-aderencia.md`
- `docs/auditoria/02-backend-aderencia.md`
- `docs/auditoria/03-frontend-aderencia.md`
