# Roteiro de Homologação Manual por Perfil (Staging)

Data: 2026-02-18
Ambiente-alvo: staging institucional

## Perfis e mapeamento

- Voluntário → papel técnico `Operador`
- Administrador → papel técnico `Admin`
- Pastoral → mapeamento temporário para `Leitura` (com possíveis permissões adicionais)

> Se papel Pastoral dedicado não existir, registrar aceite institucional do mapeamento temporário e abrir backlog para role dedicada.

---

## 4.1 Voluntário (Operador) — fluxos obrigatórios

1. Login em `/login`.
2. Busca global em `/busca` para localizar família/pessoa.
3. Criar/editar família pelo wizard (`/familias/nova/step/{step}` e `/familias/{id}/editar`).
4. Cadastrar criança vinculada (`/criancas/nova` ou contexto da família).
5. Operar evento de entrega (`/entregas/eventos`):
   - criar evento;
   - convidar famílias;
   - confirmar retirada com assinatura;
   - exportar PDF do evento.
6. Emprestar e devolver equipamento (`/equipamentos/{id}/emprestimo` e `/equipamentos/{id}/devolver`).
7. Gerar relatório PDF mensal geral (`/relatorios/*`).
8. Logout (`/logout`).

### Critério de aceite
- Sem erros funcionais.
- PDFs gerados com conteúdo coerente.
- Ações críticas registradas em `audit_logs`.

---

## 4.2 Administrador (Admin) — fluxos obrigatórios

1. Login.
2. Criar usuário e atribuir perfil (`/admin/users/new`).
3. Ajustar `system_settings`/elegibilidade (`/admin/config`).
4. Versionar termo de consentimento (`/admin/consentimento`).
5. Fechar mês (`/admin/fechamento`, ação close).
6. Gerar relatório oficial mensal (PDF + SHA256).
7. Acessar histórico mensal e gráficos (`/historico` e `/historico/{ano}/{mes}`).
8. Baixar PDF oficial e validar hash SHA256.
9. Consultar `audit_logs` por entidade (`/admin/audit`).

### Critério de aceite
- Fechamento/lock mensal funcionando.
- Relatório oficial imutável sem override.
- Hash SHA256 consistente no download oficial.

---

## 4.3 Pastoral (Leitura mapeada) — fluxos obrigatórios

1. Login.
2. Acessar pessoas e ficha social (rotas de leitura permitidas).
3. Registrar/consultar acompanhamento espiritual (quando módulo estiver disponível no ambiente).
4. Ver histórico e PDFs conforme permissões.
5. Confirmar que anotações restritas permanecem restritas.
6. Logout.

### Critério de aceite
- Perfil não consegue executar ações administrativas indevidas.
- Conteúdo sensível visível apenas conforme política institucional.

---

## Checklist de execução da homologação

- [ ] Evidência de login/logout por perfil.
- [ ] Evidência de CRUD operacional sem erro para Voluntário.
- [ ] Evidência de governança mensal para Admin.
- [ ] Evidência de restrição de acesso para Pastoral mapeado.
- [ ] Evidência de PDF oficial + hash do último mês.
- [ ] Evidência de audit_logs para operações críticas.

## Resultado da rodada

Status sugerido (preencher ao final da execução em staging):
- Voluntário: [ ] Aprovado [ ] Reprovado
- Admin: [ ] Aprovado [ ] Reprovado
- Pastoral (mapeado): [ ] Aprovado [ ] Reprovado

Observações finais:
- Registrar incidentes, prints e timestamp de execução.
- Anexar no dossiê institucional de go-live.
