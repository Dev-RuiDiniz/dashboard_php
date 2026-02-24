# Governança de dados e política LGPD (básica)

Este documento define uma base mínima para governança, versionamento e proteção de dados pessoais no contexto do Igreja Dashboard.

## 1. Governança

### 1.1 Papéis e responsabilidades

- **Controlador:** liderança responsável pelo ministério/área social que define finalidade e uso dos dados.
- **Operador:** equipe autorizada que realiza cadastro, atualização e atendimento social no sistema.
- **Administrador do sistema:** responsável por acesso, backup, restauração e trilhas de auditoria.

### 1.2 Princípios operacionais

- **Necessidade:** coletar somente dados necessários para atendimento social e relatórios internos.
- **Finalidade:** usar dados apenas para objetivos declarados (atendimento, acompanhamento e prestação de contas institucional).
- **Acesso mínimo:** aplicar RBAC já existente para limitar visualização e edição por perfil.
- **Rastreabilidade:** manter logs de autenticação e operações críticas para auditoria interna.

### 1.3 Rotina mínima de governança

- Revisão trimestral de perfis e permissões de usuários.
- Revisão semestral dos campos coletados para remover excessos.
- Inventário simples de dados (o que coletamos, por que coletamos, quem acessa).

## 2. Versionamento de dados

### 2.1 Estrutura técnica

- **Schema versionado via Alembic:** toda alteração estrutural deve gerar nova migração com histórico em `alembic/versions`.
- **Aplicação de versões:** ambientes devem executar `alembic upgrade head` antes de iniciar a aplicação.
- **Rastreio de releases:** toda implantação deve registrar commit/tag e revisão de migração aplicada.

### 2.2 Boas práticas de mudança

- Não editar migração antiga já aplicada em produção; criar nova migração incremental.
- Em mudanças destrutivas, preparar plano de rollback e backup prévio.
- Validar consistência pós-migração (contagem de registros, integridade referencial e consultas críticas).

### 2.3 Backup e recuperação

- Manter backup periódico com retenção definida (ex.: diário por 30 dias).
- Testar restauração de backup periodicamente em ambiente de homologação.
- Documentar RPO/RTO alvo conforme capacidade operacional da igreja.

## 3. Política LGPD básica

> Esta seção é uma diretriz inicial e não substitui avaliação jurídica especializada.

### 3.1 Bases e tratamento

- Definir e documentar base legal aplicável para cada tipo de dado sensível/pessoal tratado.
- Registrar finalidade de tratamento por domínio (famílias, dependentes, visitas, rua, equipamentos).
- Limitar compartilhamento de dados pessoais a pessoas autorizadas e necessidade comprovada.

### 3.2 Direitos do titular

- Disponibilizar canal para solicitação de acesso, correção e eliminação (quando aplicável).
- Registrar atendimento das solicitações com data, responsável e resultado.
- Responder solicitações em prazo interno definido e rastreável.

### 3.3 Segurança mínima

- Exigir senha forte e revisão periódica de contas ativas.
- Habilitar `COOKIE_SECURE=true` em produção com HTTPS.
- Restringir acesso administrativo e manter logs com retenção adequada.
- Evitar exportações de dados sem finalidade clara; proteger arquivos exportados.

### 3.4 Retenção e descarte

- Definir prazo de retenção por categoria de dado.
- Anonimizar ou eliminar dados quando a finalidade expirar (salvo obrigação legal de retenção).
- Garantir descarte seguro de backups fora de retenção.

### 3.5 Incidentes

- Manter procedimento básico de resposta a incidentes: identificação, contenção, análise, comunicação e lições aprendidas.
- Registrar incidente com impacto, dados afetados e medidas corretivas.

## 4. Checklist operacional mensal

- [ ] Revisar usuários e perfis de acesso.
- [ ] Confirmar execução de backup e teste de restauração.
- [ ] Conferir se migrações e versão da aplicação estão alinhadas.
- [ ] Avaliar exportações realizadas e necessidade de retenção.
- [ ] Revisar solicitações de titulares e pendências LGPD.
