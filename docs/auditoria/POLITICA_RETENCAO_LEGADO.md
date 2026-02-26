# Política de Retenção e Limpeza de Legado

## Objetivo
Definir diretriz operacional para inventariar, aprovar e remover/arquivar artefatos legados fora do runtime principal do backend PHP.

## Escopo de runtime principal (manter)
- `src/`, `public/`, `routes/`, `database/migrations/`
- `docs/`, `scripts/`, `tests/`, `.github/`

## Escopo de legado (avaliar para arquivamento/remoção)
- `frontend/legacy`
- `igreja_dashboard_python`

## Critérios de decisão
1. Confirmar que não há dependência de execução em produção.
2. Confirmar que não há dependência de pipeline CI/CD crítica.
3. Preservar trilha histórica por arquivamento versionado quando aplicável.
4. Executar remoção somente após aprovação técnica formal.

## Processo sugerido
1. Gerar inventário com `php scripts/legacy_cleanup_report.php`.
2. Revisar com equipe técnica e aprovar plano de ação.
3. Executar limpeza em janela controlada.
4. Validar regressão com `bash scripts/ci_checks.sh`.

## Evidência
- Relatório JSON gerado por `scripts/legacy_cleanup_report.php`.
