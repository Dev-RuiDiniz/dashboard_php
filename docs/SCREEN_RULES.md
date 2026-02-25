# 1. Propósito e Fonte de Verdade
Este documento é a constituição de telas do projeto e define regras fixas de UI, navegação, layout, estados, componentes, permissões e critérios de aceite.

A fonte de verdade única é o **Fluxo Completo de Telas** fornecido no escopo desta tarefa. É proibido implementar telas, campos, filtros, ações ou fluxos fora desse conteúdo.

Se houver qualquer dúvida de interpretação: **consultar o fluxo e não implementar**.

# 2. Regras Inquebráveis (Do/Don’t) — bullets curtos e objetivos
- **Do:** Implementar somente telas e fluxos listados nesta constituição.
- **Do:** Manter nomenclatura de telas e títulos padronizada.
- **Do:** Reutilizar padrões globais (Busca Global, Botão “Novo”, Chips de alerta, Timeline).
- **Do:** Respeitar perfis de acesso (voluntário/admin/pastoral).
- **Do:** Aplicar critérios de aceite Given/When/Then de cada módulo.
- **Don’t:** Não criar novos campos, status, filtros, abas, ações ou etapas.
- **Don’t:** Não alterar comportamento de status padronizados.
- **Don’t:** Não duplicar fluxo equivalente com nome diferente.
- **Don’t:** Não publicar PR com divergência desta constituição.
- **Don’t:** Em caso de dúvida, não implementar; consultar o fluxo.

# 3. Mapa de Navegação (macro e menus)
## 3.1 Fluxo macro
Login → Dashboard → (Famílias | Pessoas | Crianças | Entregas | Equipamentos | Relatórios | Usuários/Config) → Logout.

## 3.2 Menus
- Desktop: menu lateral obrigatório.
- Mobile: menu hambúrguer obrigatório.

## 3.3 Lista mínima de rotas do sistema
- `/login`
- `/recuperar-senha`
- `/dashboard`
- `/familias`
- `/familias/nova`
- `/familias/:id`
- `/pessoas`
- `/pessoas/novo-atendimento`
- `/pessoas/:id`
- `/criancas`
- `/criancas/nova`
- `/criancas/:id/editar`
- `/entregas/eventos`
- `/entregas/eventos/novo`
- `/entregas/eventos/:id/convidados`
- `/entregas/eventos/:id/criancas`
- `/equipamentos`
- `/equipamentos/novo`
- `/equipamentos/emprestimos`
- `/relatorios/mensais`
- `/admin/usuarios`
- `/admin/config`

# 4. Padrões Globais de UI (layout, grids, headers, busca global, botão “Novo”, chips, timelines)
## 4.1 Layout e grids
- Header com título da tela e ações contextuais.
- Estrutura de conteúdo com blocos: filtros, tabela/lista, ações.
- Responsividade obrigatória entre desktop e mobile.

## 4.2 Padrão de nomenclatura de telas e títulos
- Lista: `Lista de <Módulo>` (ex.: **Lista de Famílias**).
- Criação: `Nova <Entidade>` (ex.: **Nova Família**).
- Edição: `Editar <Entidade>`.
- Detalhe: `Detalhe da <Entidade>` ou `Detalhe do <Entidade>` (ex.: **Detalhe da Família**).
- Eventos: `Eventos de Entrega`, `Criar Evento de Entrega`.

## 4.3 Contrato de consistência de componentes repetidos
### Busca Global (topo)
- Escopo único: nome/CPF/RG/família.
- Presença no topo das telas internas.
- Mesmo comportamento de pesquisa em todo o sistema.

### Botão “Novo” flutuante
- Ações permitidas: Atendimento, Família, Evento, Equipamento.
- Sempre flutuante nas telas internas aplicáveis.
- Não incluir outros atalhos além dos quatro previstos.

### Chips de alerta
- Tipos permitidos: Docs pendente, Visita, Prioridade, Situação de rua.
- Estilo e nomenclatura fixos.

### Timeline
- Obrigatória em Pessoa (Fichas/Atendimentos) e Família (histórico em detalhe/abas).
- Ordem cronológica consistente.

# 5. Padrões de Formulários e Wizard (rascunho, validação, erros, salvamento, campos obrigatórios)
- Campos obrigatórios são somente os necessários para concluir etapas do fluxo definido.
- Exibir erro de validação por campo e resumo no topo quando aplicável.
- Estados de salvamento: rascunho e concluído, quando previsto no fluxo.
- Wizard da Nova Família com etapas fixas: A Responsável; B Endereço; C Socioeconômico; D Indicadores.
- Botões do wizard: `Salvar rascunho` e `Salvar e concluir`.
- Em caso de dado inválido, impedir conclusão e manter dados preenchidos.
- Consentimento em Novo Atendimento exige checkbox + assinatura simples.

# 6. Tabelas, Filtros e Ações por Linha (padrão comum)
- Tabelas com filtros no topo e ações por linha no final.
- Filtros devem corresponder exatamente aos definidos por módulo.
- Ações por linha devem corresponder exatamente às ações do fluxo.
- Ordenação e paginação podem existir sem alterar campos/ações definidos.
- Exportações devem seguir padrões de saída da seção 10.

# 7. Estados de Tela (loading, vazio, erro, permissão negada, offline se aplicável)
- **Loading:** exibir estado de carregamento antes do conteúdo.
- **Vazio:** exibir mensagem clara quando não houver registros.
- **Erro:** exibir erro de operação sem ocultar contexto da tela.
- **Permissão negada:** bloquear visualização/edição conforme perfil.
- **Offline (se aplicável):** exibir indisponibilidade e impedir ações de gravação.

# 8. Regras de Permissões por Perfil (voluntário/admin/pastoral) — definir o que cada um pode ver/editar, com base no fluxo
## 8.1 Voluntário
- Pode acessar: Dashboard, Famílias, Pessoas, Crianças, Entregas, Equipamentos, Relatórios.
- Não pode acessar: Usuários/Config.
- Em Pessoas > Detalhe: sem acesso a Anotações internas restritas por perfil.

## 8.2 Pastoral
- Pode acessar: Dashboard, Famílias, Pessoas, Crianças, Entregas, Equipamentos, Relatórios.
- Não pode acessar: Usuários/Config.
- Em Pessoas > Detalhe: pode acessar Anotações internas restritas por perfil.

## 8.3 Admin
- Pode acessar todos os módulos, incluindo Usuários/Config.
- Gerencia bloqueio por tentativas na autenticação.
- Pode criar/editar usuário, perfil e ativar/desativar em Usuários.

# 9. Regras por Módulo
## 9.1 Autenticação
### a) Telas e rotas sugeridas
- `/login`
- `/recuperar-senha`

### b) Campos/colunas/filtros
- Login: email/usuário, senha.
- Recuperar senha: Email, Nova senha.

### c) Ações e comportamentos
- Login: Entrar, Esqueci minha senha.
- Estados: erro credencial; bloqueio por tentativas (admin).
- Recuperação: Enviar link/código; definir Nova senha.

### d) Critérios de aceite (Given/When/Then)
- Given credenciais válidas, When clicar em Entrar, Then acessar Dashboard.
- Given credenciais inválidas, When clicar em Entrar, Then exibir erro credencial.
- Given usuário bloqueado por tentativas, When tentar login, Then negar acesso.

## 9.2 Dashboard
### a) Telas e rotas sugeridas
- `/dashboard`

### b) Campos/colunas/filtros
- Cards: Famílias cadastradas; Pessoas acompanhadas; Crianças cadastradas; Entregas do mês; Pendências; Equipamentos (disponível/emprestado/manutenção).
- Blocos: Alertas prioritários; Próximos eventos; Últimos atendimentos.

### c) Ações e comportamentos
- Ações rápidas: Novo atendimento; Nova família; Criar evento de entrega; Gerar listas.

### d) Critérios de aceite (Given/When/Then)
- Given acesso ao Dashboard, When abrir a tela, Then exibir todos os cards e blocos previstos.
- Given ação rápida selecionada, When clicar, Then navegar para o fluxo correspondente.

## 9.3 Famílias
### a) Telas e rotas sugeridas
- `/familias`
- `/familias/nova`
- `/familias/:id`

### b) Campos/colunas/filtros
- Lista filtros: CPF responsável, Nome responsável, Bairro/cidade, Status, Pendências.
- Nova família (wizard): A Responsável; B Endereço; C Socioeconômico; D Indicadores.
- Detalhe abas: Resumo; Membros; Entregas; Empréstimos; Anotações/Visitas; Documentos/Pendências.

### c) Ações e comportamentos
- Lista por linha: Ver detalhe, Editar, Criar entrega, Ver histórico.
- Wizard: Salvar rascunho; Salvar e concluir.
- Detalhe: Adicionar criança; Registrar entrega; Emprestar equipamento; Gerar declaração/relatório PDF simples.
- Status de família: ativa/inativa.

### d) Critérios de aceite (Given/When/Then)
- Given filtros preenchidos, When aplicar filtros, Then listar famílias compatíveis.
- Given wizard completo, When salvar e concluir, Then criar família e permitir acesso ao detalhe.
- Given detalhe da família, When executar ação permitida, Then registrar no módulo correspondente.

## 9.4 Pessoas / Atendimento Social
### a) Telas e rotas sugeridas
- `/pessoas`
- `/pessoas/novo-atendimento`
- `/pessoas/:id`

### b) Campos/colunas/filtros
- Lista filtros: Nome, CPF/RG, Situação de rua, Necessidade imediata, Último atendimento.
- Novo Atendimento: Identificação; Contato/localização; Condição atual; Situação profissional; Necessidades imediatas; Acompanhamento espiritual; Encaminhamentos (vários); Consentimento (checkbox + assinatura simples).
- Detalhe abas: Resumo; Fichas/Atendimentos (timeline); Encaminhamentos; Acompanhamento espiritual; Anotações internas (restritas por perfil).

### c) Ações e comportamentos
- Lista: Novo atendimento.
- Formulário: Salvar rascunho; Concluir; Vincular a família (opcional); Criar encaminhamento agora (modal).

### d) Critérios de aceite (Given/When/Then)
- Given formulário em preenchimento, When salvar rascunho, Then manter registro incompleto editável.
- Given consentimento preenchido, When concluir, Then registrar atendimento concluído.
- Given perfil sem permissão, When acessar Anotações internas, Then negar visualização.

## 9.5 Crianças
### a) Telas e rotas sugeridas
- `/criancas`
- `/criancas/nova`
- `/criancas/:id/editar`

### b) Campos/colunas/filtros
- Lista colunas: Nome, Idade, Responsável, Telefone, Parentesco, Família vinculada, Observações.
- Cadastro/Editar: Nome, idade; Responsável (selecionar família/responsável); Telefone auto do responsável (editável); Parentesco; Observações.

### c) Ações e comportamentos
- Lista: Nova criança; Importar/associar por família.

### d) Critérios de aceite (Given/When/Then)
- Given nova criança preenchida, When salvar, Then criar vínculo com responsável/família selecionados.
- Given ação de importar/associar, When executar, Then refletir associação na lista.

## 9.6 Entregas (Cesta)
### a) Telas e rotas sugeridas
- `/entregas/eventos`
- `/entregas/eventos/novo`
- `/entregas/eventos/:id/convidados`
- `/entregas/eventos/:id/criancas`

### b) Campos/colunas/filtros
- Eventos lista: data, tipo, status.
- Criar evento: Nome; Data; Regras (bloquear múltiplas entregas no mês on/off, limite total opcional).
- Seleção convidados: manual ou por critérios (aptos, prioridade, sem pendências, bairro); senha automática; observações por convidado.
- Lista convidados: Senha, Nome, CPF/RG, Observações, Status (Não veio/Presente/Retirou), Assinatura/Confirmar retirada.
- Lista crianças do evento: auto.

### c) Ações e comportamentos
- Eventos: criar evento.
- Operação convidados: Exportar PDF, Exportar Excel/CSV, Encerrar evento.
- Lista crianças: exportar PDF/Excel.
- Padrão de status de entrega: rascunho/aberto/concluído.
- Padrão de status de convidado: não veio/presente/retirou.

### d) Critérios de aceite (Given/When/Then)
- Given evento em rascunho, When concluir criação, Then status muda para aberto.
- Given convidado marcado como retirou, When confirmar retirada, Then registrar assinatura/confirmação.
- Given evento encerrado, When encerrar evento, Then status muda para concluído.

## 9.7 Equipamentos
### a) Telas e rotas sugeridas
- `/equipamentos`
- `/equipamentos/novo`
- `/equipamentos/emprestimos`

### b) Campos/colunas/filtros
- Lista filtros: Tipo, Status, Código.
- Cadastro: Tipo; Código (auto); Estado conservação; Observações.
- Empréstimo: família, equipamento disponível, prazo, termo, confirmar.
- Devolução: data, estado, observações, atualizar status.

### c) Ações e comportamentos
- Lista: Novo equipamento; Registrar manutenção.
- Empréstimo/Devolução: Emprestar e Devolver conforme fluxo.
- Padrão de status de equipamento: disponível/emprestado/manutenção.

### d) Critérios de aceite (Given/When/Then)
- Given equipamento disponível, When confirmar empréstimo, Then status muda para emprestado.
- Given devolução registrada, When concluir devolução, Then atualizar data/estado/observações e status.
- Given manutenção registrada, When confirmar, Then status muda para manutenção.

## 9.8 Relatórios
### a) Telas e rotas sugeridas
- `/relatorios/mensais`

### b) Campos/colunas/filtros
- Filtros: mês/ano, tipo.
- Relatórios: famílias atendidas, cestas, crianças, encaminhamentos, equipamentos, pendências/alertas.

### c) Ações e comportamentos
- Gerar PDF.
- Exportar Excel/CSV.

### d) Critérios de aceite (Given/When/Then)
- Given filtros válidos, When gerar relatório, Then retornar dados do tipo selecionado.
- Given relatório gerado, When exportar, Then baixar arquivo no formato escolhido.

## 9.9 Usuários/Config (Admin)
### a) Telas e rotas sugeridas
- `/admin/usuarios`
- `/admin/config`

### b) Campos/colunas/filtros
- Usuários: criar/editar, perfil (voluntário/admin/pastoral), ativar/desativar.
- Config: categorias encaminhamento; textos padrão; parâmetros elegibilidade; limite entregas/mês; backup (status).

### c) Ações e comportamentos
- Gerenciar usuários e perfis.
- Gerenciar parâmetros de configuração do sistema.
- Acesso restrito a admin.

### d) Critérios de aceite (Given/When/Then)
- Given usuário admin, When acessar Usuários/Config, Then permitir visualizar e editar.
- Given usuário não admin, When acessar Usuários/Config, Then negar acesso.

# 10. Saídas/Exportações (PDF/Excel/CSV): regras e nomes padrão
- Formatos permitidos: PDF, Excel, CSV conforme fluxo.
- Aplicações obrigatórias:
  - Entregas > Lista convidados: PDF e Excel/CSV.
  - Entregas > Lista crianças do evento: PDF e Excel.
  - Relatórios mensais: PDF e Excel/CSV.
  - Família (detalhe): declaração/relatório PDF simples.
- Padrão de nome de arquivo:
  - `entregas_convidados_{evento}_{YYYY-MM-DD}.{ext}`
  - `entregas_criancas_{evento}_{YYYY-MM-DD}.{ext}`
  - `relatorio_mensal_{tipo}_{YYYY-MM}.{ext}`
  - `familia_{id}_declaracao_{YYYY-MM-DD}.pdf`

# 11. Checklist de Conformidade (para usar antes de abrir PR)
- [ ] Tela/rota existe na lista mínima de rotas.
- [ ] Não há campos, colunas, filtros ou ações fora do fluxo.
- [ ] Componentes globais seguem contrato de consistência.
- [ ] Estados de tela implementados (loading, vazio, erro, permissão negada, offline se aplicável).
- [ ] Permissões por perfil respeitadas.
- [ ] Status padronizados aplicados corretamente.
- [ ] Critérios Given/When/Then do módulo atendidos.
- [ ] Exportações seguem formatos e nomes padrão.
- [ ] Em caso de dúvida, fluxo consultado e implementação não extrapolada.

---

## Auto-checagem
- Este documento contém SOMENTE regras derivadas do fluxo? **sim**
- Existe alguma tela/campo inventado? **não**
- Todas as rotas mínimas foram listadas? **sim**
