# SMOKE_TESTS_E2E

## Escopo coberto
- login (web + API)
- dashboard summary (página)
- families list
- create family (fluxo usado em testes existentes)
- create child
- create event + invite + withdraw + close
- export PDF (evento/família/relatórios)
- equipment loan + return
- timeline agregado
- logout

## Execução
```bash
pytest tests/test_auth.py tests/test_delivery_events.py -q
```

## Resultado esperado
- Todos os cenários acima devem passar em SQLite local de testes.
