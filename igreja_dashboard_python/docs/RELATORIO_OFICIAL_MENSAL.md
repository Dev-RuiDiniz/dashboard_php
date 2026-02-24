# Relatório Oficial Mensal Consolidado

## O que é
O **Relatório Oficial Mensal Consolidado** é o documento institucional definitivo para prestação de contas de uma competência mensal já fechada.

Ele consolida KPIs sociais/operacionais, comparação com mês anterior, assinatura administrativa e verificação de integridade por hash SHA256.

## Quando gerar
1. Primeiro execute o fechamento mensal (`/admin/fechamento` → **Fechar Mês**).
2. Com status `CLOSED`, execute **Gerar Relatório Oficial**.

> Regra: sem fechamento (`CLOSED`), a geração é bloqueada.

## O que o relatório contém
1. **Resumo Executivo**
2. **Indicadores Sociais**
3. **Distribuição por Bairro**
4. **Evolução comparativa com mês anterior**
5. **Assinatura digital administrativa** (simples: nome + user_id + timestamp)

## Endpoints administrativos
- `POST /admin/fechamento/{year}/{month}/gerar-relatorio-oficial`
- `GET /admin/fechamento/{year}/{month}/relatorio-oficial.pdf`
- `GET /admin/fechamento/{year}/{month}/relatorio-oficial.snapshot.json`

O download do PDF retorna o cabeçalho:
- `X-Content-SHA256: <hash_hex_64>`

## Integridade (SHA256)
Após geração:
- o PDF é salvo em `data/reports/monthly_official/{year}-{month:02d}-relatorio-oficial.pdf`;
- o hash SHA256 é persistido em `monthly_closures.official_pdf_sha256`.

Validação prática:
1. baixar o PDF oficial;
2. recalcular SHA256 localmente;
3. comparar com o valor no header `X-Content-SHA256` e no banco.

## Imutabilidade e override
Política padrão:
- se já existir `official_pdf_path`, nova geração retorna `409 Conflict`.

Exceção controlada:
- só é permitido regerar com `ADMIN_OVERRIDE=true`;
- o override gera auditoria dedicada em `audit_logs`.

## Auditoria
Ações registradas:
- `MONTHLY_OFFICIAL_REPORT_GENERATED`
- `MONTHLY_OFFICIAL_REPORT_REGENERATED` (quando override)
- `MONTHLY_OFFICIAL_REPORT_OVERRIDE` (registro explícito de uso de override)
