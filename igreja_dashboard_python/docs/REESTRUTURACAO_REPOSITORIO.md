# REESTRUTURAÇÃO DO REPOSITÓRIO

## 1) Auditoria de limpeza

### Itens identificados

- **Documentação duplicada/desatualizada**: relatórios de pré-implementação por sprint e auditorias intermediárias.
- **Material legado relevante**: histórico de decisões de sprint útil para rastreabilidade.
- **Arquivos fora de padrão principal**: documentos antigos em `docs/` sem função operacional no dia a dia.

## 2) Classificação aplicada

### A) Essencial (mantido)

- Código-fonte em `src/`
- Testes em `tests/`
- Relatórios operacionais e institucionais em `docs/` (arquitetura, módulos, segurança, LGPD, fechamento, histórico, configuração, fluxo, homologação)
- README principal e documento institucional de aceite

### B) Legado relevante (movido para `/docs/legacy`)

- `docs/SPRINT*_ANALISE_PRE_IMPLEMENTACAO.md`
- `docs/AUDITORIA_LGPD_FINAL.md`
- `docs/RELATORIO_LGPD_FINAL.md`
- `docs/AUDITORIA_FINAL_ARQUITETURA.md`

### C) Obsoleto (remoção)

- Nesta sprint extra **não houve remoção definitiva de código** para evitar risco funcional.
- Itens obsoletos remanescentes foram tratados via segregação em `docs/legacy`.

## 3) Estrutura final padronizada

Estrutura alvo confirmada:

```text
/src
/docs
/docs/legacy
/data/reports
/tests
README.md
DOCUMENTO_ACEITE_INSTITUCIONAL.md
```

## 4) Resultado

- Repositório organizado em documentação **operacional atual** e **acervo histórico**.
- Redução de ruído no diretório `docs/` principal.
- Base pronta para homologação e manutenção contínua.
