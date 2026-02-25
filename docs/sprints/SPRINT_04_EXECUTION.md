# Sprint 04 — Plano Operacional de Execução

## 1) Escopo da sprint

### Entra na Sprint 04
- CRUD de domínio social para:
  - `/families`
  - `/dependents`
  - `/children`
- Validação de CPF para cadastro de responsável de família.
- Regra de unicidade de CPF de responsável na coleção de famílias.
- Integridade mínima entre entidades (dependente/criança deve referenciar família existente).
- Auditoria de alterações cadastrais.

### Não entra na Sprint 04
- Persistência em banco e migrações.
- Telas SSR/UX.
- Campos além do necessário para cumprir CRUD mínimo da sprint.

## 2) Referências obrigatórias
- `AUDITORIA_E_PLANO_MIGRACAO_PYTHON_PHP_10_SPRINTS.md` (Sprint 04).
- `docs/DB_RULES_MYSQL.md`.
- `docs/SCREEN_RULES.md`.

## 3) Objetivo e backlog

### Objetivo
- Entregar domínio base social na stack PHP com validações essenciais e consistência.

### Backlog
- CRUD famílias/dependentes/crianças.
- Validações CPF/documentos.
- Constraints de integridade.

### Critérios de aceite
- Regras de unicidade e consistência replicadas.
- Testes de CRUD + validação CPF + integridade.

## 4) Ordem de execução
1. Documento da sprint.
2. Implementação do store de domínio + validação CPF.
3. Endpoints de domínio no kernel.
4. Auditoria de eventos cadastrais.
5. Testes automatizados.
6. Relatório final da sprint.

## 5) Checklist
- [x] Implementar validação de CPF.
- [x] Implementar store de famílias/dependentes/crianças.
- [x] Implementar endpoints de CRUD mínimo da sprint.
- [x] Validar unicidade de CPF em famílias.
- [x] Validar integridade de referência family_id.
- [x] Registrar auditoria de alterações cadastrais.
- [x] Adicionar testes automatizados da sprint.
- [x] Produzir `docs/sprints/SPRINT_04_REPORT.md`.

## 6) Plano de testes
- Criar família com CPF válido retorna sucesso.
- Criar família com CPF inválido retorna erro de validação.
- Criar família com CPF duplicado retorna conflito.
- CRUD de dependente e criança exige `family_id` existente.
- Perfil leitura não pode executar escrita cadastral.
- Auditoria é registrada para operações de alteração.

## 7) Rollback
- Reverter commit da sprint.
- Sem rollback de banco (não há migração nesta sprint).
