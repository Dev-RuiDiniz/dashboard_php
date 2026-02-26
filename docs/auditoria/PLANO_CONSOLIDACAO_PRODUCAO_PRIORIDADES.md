# Plano de Consolidação e Envio para Produção (por Prioridades)

## Objetivo
Consolidar o sistema e realizar o go-live em produção (Hostinger) com risco controlado, obedecendo a especificação oficial e os gates técnicos do projeto.

---

## Visão geral de prioridades

- **P0 (Crítico / bloqueia produção):** segurança, dados, infraestrutura mínima, go/no-go técnico.
- **P1 (Alto / obrigatório para operação estável):** operação assistida, observabilidade, rotinas de backup/restauração, validação funcional fim-a-fim.
- **P2 (Médio / consolidação pós-go-live):** melhorias de UX, fechamento de gaps não críticos, performance e governança contínua.

---

## P0 — Pré-Go-Live obrigatório (Bloqueador)

### 1) Segurança e configuração de ambiente
- [ ] Definir `APP_ENV=production` e `APP_READY=true`.
- [ ] Definir `JWT_SECRET` forte e exclusivo do ambiente.
- [ ] Garantir variáveis de banco (`MYSQL_DSN` ou `MYSQL_*`) com usuário de privilégio mínimo.
- [ ] Rotacionar/remover credenciais bootstrap de uso padrão (`admin@local`, etc.) no ambiente produtivo.
- [ ] Forçar HTTPS e validar cabeçalhos de segurança no servidor web.

**Critério de saída (DoD P0.1):** nenhum segredo hardcoded, autenticação operacional, acesso apenas via HTTPS.

### 2) Banco de dados e integridade
- [ ] Executar `php scripts/run_migrations.php` em staging homologado e, depois, em produção.
- [ ] Executar `php scripts/migrate_json_to_mysql.php` (quando houver legado JSON a consolidar).
- [ ] Executar `php scripts/reconciliation_report.php` e arquivar resultado.
- [ ] Validar consistência relacional e contagens críticas (famílias, visitas, eventos, empréstimos).

**Critério de saída (DoD P0.2):** schema aplicado, dados reconciliados e sem divergência crítica aberta.

### 3) Gate técnico de prontidão
- [ ] Executar `bash scripts/ci_checks.sh` e obter 100% de sucesso.
- [ ] Executar `php scripts/security_posture_report.php` sem pendência crítica de configuração.
- [ ] Executar `php scripts/pilot_cutover_dry_run.php` com decisão **GO**.
- [ ] Executar `php scripts/handover_closure_report.php` e anexar evidências.

**Critério de saída (DoD P0.3):** dry-run aprovado (GO), evidências versionadas/documentadas, sem bloqueio crítico.

---

## P1 — Estabilização operacional (Obrigatório para operação segura)

### 4) Smoke funcional orientado ao negócio
Executar roteiro com perfis distintos (admin, operador, leitura):
- [ ] Login, `/me`, logout.
- [ ] CRUD de famílias/dependentes/crianças.
- [ ] Cadastro e conclusão de atendimento street com consentimento.
- [ ] Evento de entrega + convite + retirada com assinatura.
- [ ] Empréstimo/devolução de equipamento.
- [ ] Solicitação e conclusão de visita.
- [ ] Exportações (`CSV`, `XLSX`, `PDF`) e relatórios mensais.

**Critério de saída (DoD P1.1):** roteiro de smoke 100% OK com evidência (data/hora, usuário, resultado).

### 5) Backup, restauração e rollback
- [ ] Implementar rotina de backup (full + retenção mínima definida).
- [ ] Executar teste real de restauração em ambiente de homologação.
- [ ] Definir procedimento de rollback (tag de release + snapshot DB + validação pós-retorno).

**Critério de saída (DoD P1.2):** restauração comprovada e rollback testado/documentado.

### 6) Observabilidade e suporte inicial
- [ ] Centralizar logs de aplicação e erros do servidor.
- [ ] Definir monitoração mínima (`/health`, `/ready`, erros 5xx, falhas login excessivas).
- [ ] Estabelecer janela de hiper-care (ex.: 7 dias) com responsáveis e SLA interno.

**Critério de saída (DoD P1.3):** operação monitorada com donos claros e canal de resposta.

---

## P2 — Consolidação pós-go-live (Evolução contínua)

### 7) Fechamento de gaps funcionais não bloqueantes
- [ ] Expandir UX/telas server-side conforme backlog oficial.
- [ ] Refinar matriz RBAC completa por módulo/ação (incluindo perfil pastoral, se exigido no rollout institucional).
- [ ] Revisar cobertura campo-a-campo da modelagem frente à especificação consolidada.

**Critério de saída (DoD P2.1):** gaps priorizados com aceite de produto e cronograma fechado.

### 8) Performance e governança
- [ ] Revisar índices para filtros de maior uso em produção.
- [ ] Definir rotina de revisão mensal de segurança (segredos, permissões, logs).
- [ ] Criar ciclo de release previsível (cadência, changelog, checklist de deploy).

**Critério de saída (DoD P2.2):** baseline de performance e governança recorrente implantada.

---

## Sequência recomendada (cronológica)

1. **Semana 1 (P0):** segurança/env + migrations/reconciliação + gates técnicos.
2. **Semana 2 (P1):** smoke fim-a-fim + backup/restauração + observabilidade + hiper-care.
3. **Semana 3+ (P2):** melhorias estruturais, UX e governança contínua.

---

## Matriz simples de decisão de go-live

- **GO:** todos os itens P0 completos + smoke mínimo aprovado.
- **GO CONDICIONAL:** P0 completo, mas com pendências P1 sem risco crítico imediato e plano de ação datado.
- **NO-GO:** qualquer item P0 pendente ou falha de integridade/segurança.

---

## Responsáveis sugeridos

- **Tech Lead:** gate técnico, qualidade de release, rollback.
- **DBA/Responsável de dados:** migrations, reconciliação e backup/restauração.
- **PO/Coordenação social:** validação funcional e aceite operacional.
- **DevOps/Infra (ou equivalente Hostinger):** HTTPS, variáveis, monitoramento e logs.

---

## Evidências mínimas para auditoria final de produção

- Relatórios gerados pelos scripts de segurança/cutover/handover.
- Registro de execução dos comandos críticos com timestamp.
- Checklist assinado (P0/P1) com responsáveis.
- Tag de release e hash do commit implantado.
