# DOCUMENTO DE ACEITE INSTITUCIONAL

## 1) Identificação

- Sistema: Gestão da Ação Social — Primeira Igreja Batista de Taubaté
- Versão: 0.1.0 (baseline pós Sprints 0–10)
- Data do aceite: ____/____/______

## 2) Escopo entregue (módulos)

- Autenticação, RBAC e administração de usuários
- Gestão de famílias e dependentes
- Gestão de crianças
- Entregas por evento (convite, retirada com assinatura, exportações)
- Gestão de equipamentos (empréstimo/devolução)
- Atendimento de pessoas em situação de rua
- Relatórios institucionais (CSV/XLSX/PDF)
- Fechamento mensal com lock
- Relatório oficial mensal com hash SHA256
- Histórico mensal imutável com análise gráfica
- Governança LGPD (consentimento + trilha de auditoria)

## 3) Critérios atendidos

- [x] PDFs universais
- [x] Fechamento mensal + lock
- [x] Relatório oficial + SHA256
- [x] Histórico imutável + gráficos
- [x] LGPD (consentimento + audit trail)
- [x] Segurança (reset senha, lockout, rate-limit)

## 4) Pendências conhecidas

1. **Drift em `alembic check` (SQLite) para FKs de `monthly_closures`**
   - Severidade: Média
   - Prazo recomendado: próxima sprint técnica
2. **Validação local com PostgreSQL indisponível neste ambiente de execução**
   - Severidade: Média
   - Prazo recomendado: antes da virada de staging para produção
3. **Papel Pastoral dedicado não formalizado como role própria**
   - Severidade: Baixa
   - Prazo recomendado: backlog de governança de acesso

## 5) Declaração de aceite

Declaro que o sistema foi avaliado conforme critérios institucionais e está:

- [ ] APROVADO para uso oficial
- [ ] APROVADO COM RESSALVAS
- [ ] NÃO APROVADO

Responsável (Admin): ____________________________________

Cargo/Ministério: _______________________________________

Data: ____/____/______

Assinatura (nome digitado): ______________________________

## 6) Anexo — artefatos oficiais

- Exemplo de PDF oficial do último mês: `data/reports/official/{YYYY}/{MM}/relatorio_oficial_{YYYY}_{MM}.pdf`
- Exemplo de PDF de fechamento do último mês: `data/reports/monthly/{YYYY}/{MM}/fechamento_{YYYY}_{MM}.pdf`
- Hash SHA256 do PDF oficial (último mês): `PREENCHER_APÓS_GERAÇÃO_EM_STAGING`

