# Fechamento Mensal

O fechamento mensal cria um **registro oficial de fechamento** do mês com:
1. Snapshot consolidado em JSON (`monthly_closures.summary_snapshot_json`)
2. PDF de fechamento persistido em disco (`monthly_closures.pdf_report_path`)
3. Bloqueio de alterações retroativas para o mês fechado

## Como fechar mês (Admin)
1. Acessar `/admin/fechamento`
2. Selecionar mês/ano
3. Clicar em **Fechar Mês**

Fluxo executado:
- valida mês aberto
- gera snapshot consolidado
- gera PDF de fechamento via engine institucional
- salva PDF em `REPORTS_DIR/monthly/{year}-{month:02d}-fechamento.pdf`
- persiste `monthly_closures` com status `CLOSED`
- registra `audit_logs` com ação `MONTH_CLOSE`

## Etapa adicional (Sprint 8): Gerar Relatório Oficial
Após o fechamento (`CLOSED`), execute:
- botão **Gerar Relatório Oficial** na mesma tela `/admin/fechamento`, ou
- `POST /admin/fechamento/{year}/{month}/gerar-relatorio-oficial`.

Resultado:
- gera snapshot oficial com comparativo mês anterior
- gera PDF oficial institucional
- salva arquivo em `REPORTS_DIR/monthly_official/{year}-{month:02d}-relatorio-oficial.pdf`
- calcula e persiste hash SHA256 (`official_pdf_sha256`)
- registra assinatura administrativa (`official_signed_by_user_id`, `official_signed_at`)

Endpoints de consulta:
- `GET /admin/fechamento/{year}/{month}/relatorio-oficial.pdf`
- `GET /admin/fechamento/{year}/{month}/relatorio-oficial.snapshot.json`

## Imutabilidade
- Relatório oficial é imutável por padrão após geração (`409` em nova tentativa).
- Regeração só é permitida com `ADMIN_OVERRIDE=true`, com auditoria especial.

## O que fica bloqueado
Consulte `docs/MONTHLY_LOCK_RULES.md`.
Resumo:
- confirmações/alterações de entregas do mês
- cestas legadas do mês
- atendimentos/encaminhamentos/visitas do mês
- operações de equipamento relacionadas ao mês

## Como baixar PDF de fechamento
- `GET /admin/fechamento/{year}/{month}/pdf`

## Como consultar snapshot de fechamento
- `GET /admin/fechamento/{year}/{month}/snapshot.json`
