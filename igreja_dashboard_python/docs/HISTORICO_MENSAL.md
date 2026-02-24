# Histórico Mensal e Análise Comparativa

## Visão geral

O módulo de histórico mensal consolida os meses cadastrados em `monthly_closures`, exibindo KPIs congelados por competência e acesso ao PDF oficial quando existente.

## Como acessar

- Lista histórica: `GET /historico`
- Detalhe do mês: `GET /historico/{year}/{month}`
- Séries para gráficos: `GET /api/historico/series?from=YYYY-MM&to=YYYY-MM`

## Interpretação das métricas

Na tabela e no detalhe, os KPIs exibidos são:
- **Famílias** (`totals.families_attended`)
- **Cestas** (`totals.deliveries_count`)
- **Crianças** (`totals.children_count`)
- **Encaminhamentos** (`totals.referrals_count`)

No detalhe também pode aparecer:
- **Média de vulnerabilidade** (`indicators.avg_vulnerability` ou fallback `totals.avg_vulnerability`)

## Origem dos dados

Para cada mês, a fonte é escolhida nesta ordem:
1. `official_snapshot_json` (quando relatório oficial foi gerado)
2. `summary_snapshot_json` (snapshot do fechamento)
3. default com zeros (mês sem snapshot)

> Importante: meses fechados (`CLOSED`) não são recalculados no histórico; a leitura é sempre dos snapshots persistidos.

## PDF oficial e verificação de hash

No detalhe do mês:
- botão **Baixar PDF oficial** aponta para `/admin/fechamento/{year}/{month}/relatorio-oficial.pdf`;
- são exibidos assinatura e hash SHA256 persistidos no fechamento oficial.

Ao baixar o PDF oficial, o backend inclui o header:
- `X-Content-SHA256: <hash>`

Isso permite comparar o hash exibido na interface com o hash recebido no download e validar integridade do artefato.

## Permissões (RBAC)

- **Admin / Operador / Leitura**: podem ver `/historico`, detalhe e consumir `/api/historico/series`.
- **Admin**: pode baixar snapshot técnico JSON (`/historico/{year}/{month}/snapshot.json`).
