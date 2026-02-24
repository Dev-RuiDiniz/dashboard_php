# GUIA DE USO DO SISTEMA

## Voluntário (perfil Operador)

1. Acessar `/login`.
2. Consultar `/dashboard` para visão geral.
3. Cadastrar/atualizar família em `/familias`.
4. Registrar dependentes e crianças.
5. Operar entregas por evento em `/entregas`.
6. Registrar empréstimos/devoluções em `/equipamentos`.
7. Emitir relatórios permitidos em `/relatorios`.

**Print simulado 1**: Tela de dashboard com indicadores e elegibilidade.
**Print simulado 2**: Lista de famílias com ações principais.

## Administrador

1. Executar todos os passos de Operador.
2. Gerenciar usuários em `/admin/users`.
3. Ajustar parâmetros em `/admin/config`.
4. Atualizar termo LGPD em `/admin/consentimento`.
5. Auditar eventos em `/admin/audit`.
6. Fechar mês em `/admin/fechamento`.
7. Gerar relatório oficial mensal e conferir SHA256.

**Print simulado 3**: Tela de fechamento mensal com status e ações.

## Pastoral (perfil Leitura)

1. Acessar `/dashboard`, `/familias` e `/historico` em modo leitura.
2. Consultar relatórios permitidos.
3. Sem permissão para ações de cadastro/edição/fechamento.

**Print simulado 4**: Tela de histórico mensal comparativo.

## Sequência lógica recomendada de operação mensal

1. Atendimento e registros ao longo do mês.
2. Geração de relatórios operacionais.
3. Fechamento mensal administrativo.
4. Emissão do relatório oficial com hash.
5. Consulta histórica para análise comparativa.
