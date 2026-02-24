# PDF Engine Institucional

## Visão geral

O projeto adota um motor central de PDF em `src/app/pdf/report_engine.py` com a função:

```python
generate_report_pdf(
    title: str,
    month: int | None,
    year: int | None,
    sections: list[dict],
    metadata: dict,
) -> bytes
```

Esse motor é usado por todos os endpoints `.pdf` de relatórios e exportações institucionais.

## Padrão institucional

Cada PDF segue o layout padrão:

- **Cabeçalho**
  - Logo institucional (arquivo estático quando disponível, com fallback placeholder);
  - Nome do sistema: `Sistema de Gestão da Ação Social`;
  - Nome da instituição;
  - período (mês/ano quando aplicável);
  - data de geração;
  - usuário que gerou o documento.
- **Corpo**
  - seções tipadas (`text` e `table`);
  - tabelas com cabeçalho e dados normalizados;
  - seção de totalizadores quando aplicável.
- **Rodapé**
  - `Página X de Y`;
  - texto institucional automático.

## Estrutura de `sections`

### Seção de texto

```python
{
  "type": "text",
  "title": "Resumo",
  "content": "Texto do resumo"
}
```

### Seção de tabela

```python
{
  "type": "table",
  "title": "Famílias Atendidas",
  "headers": ["Responsável", "CPF", "Status"],
  "rows": [
    ["Maria", "12345678901", "Ativa"],
    ["João", "10987654321", "Ativa"]
  ]
}
```

## Metadata

Exemplo padrão:

```python
metadata = {
  "generated_by": current_user.name,
  "generated_at": datetime.now(),
  "institution": "Primeira Igreja Batista de Taubaté",
}
```

## Como criar um novo relatório PDF

1. Montar os dados do relatório (normalmente reutilizando a mesma fonte de CSV/XLSX).
2. Construir `sections` com uma ou mais seções `table`/`text`.
3. Incluir seção de totalizadores ao final para relatórios agregados.
4. Chamar `generate_report_pdf(...)`.
5. Retornar `Response(..., media_type="application/pdf")`.

## Endpoints padronizados Sprint 6

- `/relatorios/familias.pdf`
- `/relatorios/cestas.pdf`
- `/relatorios/criancas.pdf`
- `/relatorios/encaminhamentos.pdf`
- `/relatorios/equipamentos.pdf`
- `/relatorios/pendencias.pdf`
- `/entregas/eventos/{id}/export.pdf`
- `/entregas/eventos/{id}/criancas/export.pdf`
- `/familias/{id}/export.pdf`
- `/pessoas/{id}/export.pdf`
