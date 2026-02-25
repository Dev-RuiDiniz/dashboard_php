# Especificação Oficial Extraída (Fonte de Verdade)

Documento-fonte analisado: `Especificacao_Sistema_Igreja_Social_PHP_MySQL.docx`.

## 1) Estrutura oficial consolidada

## 1.1 Módulos oficiais
1. Autenticação (login, recuperação de senha, bloqueio por tentativas, redefinição por token).
2. Dashboard operacional (cards, alertas, ações rápidas).
3. Famílias (lista, cadastro/edição, detalhe com abas e indicadores).
4. Pessoas acompanhadas / ficha social (lista, novo atendimento, detalhe com timeline e encaminhamentos).
5. Crianças (lista, cadastro/edição, vínculo com família).
6. Entregas de cestas (eventos, convidados, operação de retirada, exportações).
7. Equipamentos de mobilidade (cadastro, status, empréstimos/devoluções e alertas).
8. Visitas e pendências (solicitação, conclusão, observações, alertas automáticos).
9. Usuários e configurações (admin).

## 1.2 Telas oficiais
- Login.
- Recuperar senha.
- Dashboard.
- Lista/Nova-Editar/Detalhe de famílias.
- Lista/Novo atendimento/Detalhe de pessoas.
- Lista/Cadastro-Edição de crianças.
- Eventos/Criar evento/Convidados/Operacional de entregas.
- Lista/Cadastro/Empréstimos de equipamentos.
- Lista de visitas.
- Usuários e configurações administrativas.

## 1.3 Campos oficiais (macro)
- **Usuários:** nome, e-mail, hash de senha, perfil RBAC, ativo, timestamps.
- **Famílias:** dados pessoais, endereço completo, socioeconômico, documentação, pendências, visita, indicadores.
- **Membros/Crianças:** vínculos por família, dados básicos e renda (membros).
- **Pessoas/ficha social:** identificação, situação social, necessidades, consentimento LGPD, espiritual, encaminhamentos.
- **Entregas:** evento, regras do evento, convidados/retiradas, ticket/senha, assinatura e status.
- **Equipamentos/empréstimos:** inventário, condição/status, empréstimo e devolução.
- **Visitas/auditoria:** solicitações e logs de ações.

## 1.4 Regras de negócio oficiais
- CPF único para família e pessoa quando informado; permitir cadastro parcial em situação de rua.
- Bloqueio mensal de cesta quando regra ativa no evento.
- Ticket sequencial por evento, imutável após publicação da lista.
- Fluxo de status da entrega `nao_veio -> presente -> retirou` com assinatura/data/usuário na retirada.
- Consistência de status de equipamentos em empréstimo/devolução.
- Alertas de pendência documental, visita pendente, devolução vencida e desatualização de cadastro.
- Cálculo/cache de renda familiar somando rendas de membros.
- Consentimento obrigatório em ficha social.

## 1.5 Relatórios oficiais
- Famílias atendidas por período.
- Cestas entregues por evento/período.
- Crianças atendidas com vínculo familiar e evento.
- Encaminhamentos por tipo/status.
- Equipamentos emprestados/devolvidos/atrasados/manutenção.
- Pendências (documentação e visitas).

## 1.6 Permissões oficiais
Perfis: `Administrador`, `Voluntário/Operador`, `Pastoral`, `Visualizador (opcional)`.
Permissões por módulo + ação (`ver/criar/editar/excluir`) com checagem por rota/ação.

## 1.7 Integrações oficiais
- API de CEP (consulta de endereço por CEP).
- Exportações: CSV/XLSX via PHPSpreadsheet e PDF via Dompdf/mPDF.

---

## 2) Tabela de requisitos numerados (REQ)

| ID | Requisito oficial | Origem DOCX (seção/linha extraída) |
|---|---|---|
| REQ-001 | Sistema deve operar em PHP + MySQL/MariaDB (Hostinger). | Seção 1 / L2, L26-L29 |
| REQ-002 | Deve existir módulo de autenticação com login. | Seção 3.1 / L38-L39 |
| REQ-003 | Deve existir recuperação de senha por link/código. | Seção 3.1 / L40 |
| REQ-004 | Login com bloqueio por tentativas configurável. | Seção 3.1 / L41 |
| REQ-005 | Dashboard com cards operacionais (famílias, pessoas, crianças, entregas, encaminhamentos, equipamentos). | Seção 3.2 / L43 |
| REQ-006 | Dashboard com alertas (documentos, visita, desatualização, devolução atrasada). | Seção 3.2 / L44 |
| REQ-007 | Dashboard com ações rápidas (nova família, novo atendimento, evento, empréstimo). | Seção 3.2 / L45 |
| REQ-008 | Famílias: tela de lista com filtros (CPF, nome, bairro/cidade, status, pendências). | Seção 3.3 / L47 |
| REQ-009 | Famílias: nova/editar em wizard ou seções. | Seção 3.3 / L48 |
| REQ-010 | Famílias: detalhe com abas Resumo/Membros/Crianças/Entregas/Empréstimos/Visitas/Pendências. | Seção 3.3 / L49 |
| REQ-011 | Validação de CPF e bloqueio de duplicidade em famílias. | Seção 3.3 / L50 |
| REQ-012 | Calcular renda total e indicadores da família. | Seção 3.3 / L50 |
| REQ-013 | Pessoas: lista com filtros (nome, CPF/RG, situação de rua, necessidade, último atendimento). | Seção 3.4 / L52 |
| REQ-014 | Pessoas: novo atendimento em formulário por seções. | Seção 3.4 / L53 |
| REQ-015 | Pessoas: detalhe com timeline e encaminhamentos/espiritual. | Seção 3.4 / L54 |
| REQ-016 | Consentimento digital obrigatório na ficha social. | Seção 3.4 / L55 e Seção 5 / L656 |
| REQ-017 | Crianças: lista com nome/idade/responsável/telefone/parentesco/família. | Seção 3.5 / L57 |
| REQ-018 | Crianças: cadastro/edição vinculada à família. | Seção 3.5 / L58 |
| REQ-019 | Geração automática de lista de crianças por evento. | Seção 3.5 / L59 |
| REQ-020 | Entregas: eventos de entrega (lista/calendário). | Seção 3.6 / L61 |
| REQ-021 | Entregas: criação de evento com regras (bloqueio mensal e limite opcional). | Seção 3.6 / L62 |
| REQ-022 | Entregas: seleção de convidados manual ou por critérios. | Seção 3.6 / L63 |
| REQ-023 | Entregas: lista operacional com senha/documento/status/assinatura. | Seção 3.6 / L64 |
| REQ-024 | Exportação de entregas em PDF/CSV/Excel + impressão padronizada. | Seção 3.6 / L65 |
| REQ-025 | Equipamentos: lista com filtros tipo/status/código. | Seção 3.7 / L67 |
| REQ-026 | Equipamentos: cadastro com código automático e estado de conservação. | Seção 3.7 / L68 |
| REQ-027 | Equipamentos: fluxo de empréstimo/devolução com prazos e observações. | Seção 3.7 / L69 |
| REQ-028 | Equipamentos: alertas de devolução vencida e manutenção. | Seção 3.7 / L70 |
| REQ-029 | Visitas: lista de pendentes e concluídas. | Seção 3.8 / L72 |
| REQ-030 | Visitas: solicitar visita e registrar conclusão com data/usuário. | Seção 3.8 / L73 |
| REQ-031 | Usuários admin: criar/editar/perfil/ativar/desativar/redefinir senha. | Seção 3.9 / L76 |
| REQ-032 | Configurações admin: encaminhamentos, texto de termo, elegibilidade, limites, status de backup. | Seção 3.9 / L77 |
| REQ-033 | RBAC com perfis admin/voluntário-poperador/pastoral/viewer. | Seção 2 / L31-L35 |
| REQ-034 | Permissões por módulo e por ação (ver/criar/editar/excluir). | Seção 2 / L36 |
| REQ-035 | Regra CPF único e bloqueio de duplicidade. | Seção 5 / L649 |
| REQ-036 | Regra de bloqueio mensal de cestas quando ativo no evento. | Seção 5 / L650 |
| REQ-037 | Regra de ticket sequencial por evento. | Seção 5 / L651 |
| REQ-038 | Regra de fluxo de status de entrega + assinatura/data/usuário. | Seção 5 / L652 |
| REQ-039 | Regra de consistência de status de equipamento em empréstimo/devolução. | Seção 5 / L653 |
| REQ-040 | Alertas operacionais (documentação, visitas, devoluções, atualização). | Seção 5 / L654 |
| REQ-041 | Relatórios mensais por mês/ano e bairro/status. | Seção 6 / L658-L664 |
| REQ-042 | Exportações CSV/Excel/PDF com bibliotecas definidas. | Seção 6 / L665 |
| REQ-043 | Segurança: senha em hash forte, RBAC por ação, prepared statements, auditoria de ações relevantes. | Seção 7 / L667-L671 |
| REQ-044 | LGPD: consentimento digital, restrição por perfil, exportações restritas, backup protegido. | Seção 7 / L672 |
| REQ-045 | Deploy: `.env`, HTTPS, backups e `document root` em `/public`. | Seção 8 / L675-L678 |

