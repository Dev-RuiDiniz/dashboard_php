# RELATÓRIO LGPD FINAL — Sprint 10

Data: 2026-02-18
Sistema: Gestão da Ação Social — Primeira Igreja Batista de Taubaté

## 1) O que coletamos

- Dados cadastrais de famílias e responsáveis (nome, CPF, RG, contato, endereço).
- Dados socioassistenciais (vulnerabilidade, perfil socioeconômico, documentação, dependentes).
- Dados de pessoas em situação de rua (identificação quando disponível, local de referência, atendimentos e encaminhamentos).
- Dados operacionais de entrega/retirada, empréstimo/devolução e fechamento mensal.
- Dados de autenticação e segurança (usuários, tentativas de login, tokens de reset hash).

## 2) Por que coletamos

- Prestação de assistência social com critérios transparentes de elegibilidade.
- Continuidade do atendimento e priorização por vulnerabilidade.
- Prestação de contas institucional com rastreabilidade e histórico.
- Segurança de acesso ao sistema e prevenção de abuso.

## 3) Como armazenamos

- Banco relacional com domínios de autenticação e dados sociais.
- Consentimento digital versionado por termo ativo em `consent_terms`.
- Aceite de consentimento gravado por registro (`consent_accepted`, versão, timestamp e usuário).
- Artefatos oficiais (PDF fechamento/oficial) armazenados em `REPORTS_DIR`.

## 4) Como auditamos

- Trilha `audit_logs` para ações críticas via `log_action`.
- Sanitização de payload para não persistir senha/token e mascarar CPF.
- Ações auditadas no escopo crítico incluem:
  - criar/editar/remover entidades-chave (família, rua, equipamentos, eventos)
  - confirmar retirada em evento
  - emprestar/devolver equipamento
  - fechar mês
  - gerar relatório oficial

## 5) Como exportamos (PDF oficial + hash)

- PDF de fechamento mensal e relatório oficial mensal gerados e persistidos.
- Relatório oficial inclui hash SHA256 para verificação de integridade.
- Download oficial retorna cabeçalho de hash para conferência institucional.

## 6) Consentimento digital obrigatório (família/ficha social/rua)

- Fluxos de criação de família e pessoa em situação de rua exigem aceite de consentimento ativo.
- Termo é versionado e administrável por tela de administração (`/admin/consentimento`).
- Evidência de aceite vinculada a usuário e timestamp.

## 7) Retenção e backup

- Procedimentos operacionais documentados em `docs/governanca_dados_lgpd.md` e `docs/producao_hardening.md`.
- Scripts de backup/restore disponíveis em `scripts/db_backup.py` e `scripts/db_restore.py`.
- Recomendação institucional: política formal de retenção com periodicidade de backup e teste de restauração trimestral.

## 8) Controle de PII em telas e logs

- RBAC restringe leitura/edição por papel.
- Sanitização em payload de auditoria remove campos sensíveis.
- Recomendação: revisão periódica de templates para mascaramento adicional em telas de consulta operacional, conforme necessidade pastoral.

## 9) Checklist de conformidade operacional

- [x] Consentimento obrigatório implementado em fluxos críticos.
- [x] Termo versionado e administrável.
- [x] Audit trail persistente para operações críticas.
- [x] Export institucional com PDF oficial + hash.
- [x] Controle de acesso por RBAC.
- [x] Procedimento de backup/restore documentado.
- [ ] Política institucional formal de retenção (documento administrativo externo, recomendado).

## 10) Conclusão

A plataforma está **substancialmente conforme LGPD para operação institucional**, com recomendação de formalização contínua de governança documental (retenção e revisão periódica de acessos).
