<?php

declare(strict_types=1);

return [
    ['uri' => '/login', 'view' => 'pages/generic', 'title' => 'Login', 'breadcrumbs' => ['Autenticação', 'Login'], 'stub' => 'SPRINT-03 auth ui stub'],
    ['uri' => '/recuperar-senha', 'view' => 'pages/generic', 'title' => 'Recuperar senha', 'breadcrumbs' => ['Autenticação', 'Recuperar senha'], 'stub' => 'SPRINT-03 auth ui stub'],
    ['uri' => '/dashboard', 'view' => 'pages/generic', 'title' => 'Dashboard', 'breadcrumbs' => ['Dashboard'], 'chips' => ['Docs pendente', 'Visita', 'Prioridade', 'Situação de rua'], 'stub' => 'SPRINT-09 indicadores e métricas'],

    ['uri' => '/familias', 'view' => 'pages/generic', 'title' => 'Lista de Famílias', 'breadcrumbs' => ['Famílias', 'Lista'], 'table' => true, 'filters' => ['Responsável', 'CPF', 'Bairro', 'Vulnerabilidade'], 'stub' => 'SPRINT-04 integração listagem'],
    ['uri' => '/familias/nova', 'view' => 'pages/generic', 'title' => 'Nova Família', 'breadcrumbs' => ['Famílias', 'Nova Família'], 'stub' => 'SPRINT-04 wizard A/B/C/D'],
    ['uri' => '/familias/{id}', 'view' => 'pages/generic', 'title' => 'Detalhe da Família', 'breadcrumbs' => ['Famílias', 'Detalhe da Família'], 'timeline' => true, 'stub' => 'SPRINT-04 detalhe + histórico'],

    ['uri' => '/pessoas', 'view' => 'pages/generic', 'title' => 'Lista de Pessoas', 'breadcrumbs' => ['Pessoas', 'Lista'], 'table' => true, 'filters' => ['Nome', 'CPF', 'Situação', 'Último atendimento'], 'stub' => 'SPRINT-05 integração listagem'],
    ['uri' => '/pessoas/novo-atendimento', 'view' => 'pages/generic', 'title' => 'Novo Atendimento', 'breadcrumbs' => ['Pessoas', 'Novo Atendimento'], 'stub' => 'SPRINT-05 consentimento + assinatura'],
    ['uri' => '/pessoas/{id}', 'view' => 'pages/generic', 'title' => 'Detalhe da Pessoa', 'breadcrumbs' => ['Pessoas', 'Detalhe da Pessoa'], 'timeline' => true, 'stub' => 'SPRINT-05 timeline fichas/atendimentos'],

    ['uri' => '/criancas', 'view' => 'pages/generic', 'title' => 'Lista de Crianças', 'breadcrumbs' => ['Crianças', 'Lista'], 'table' => true, 'filters' => ['Nome', 'Idade', 'Família', 'Evento'], 'stub' => 'SPRINT-04 crianças listagem'],
    ['uri' => '/criancas/nova', 'view' => 'pages/generic', 'title' => 'Nova Criança', 'breadcrumbs' => ['Crianças', 'Nova Criança'], 'stub' => 'SPRINT-04 crianças cadastro'],
    ['uri' => '/criancas/{id}/editar', 'view' => 'pages/generic', 'title' => 'Editar Criança', 'breadcrumbs' => ['Crianças', 'Editar Criança'], 'stub' => 'SPRINT-04 crianças edição'],

    ['uri' => '/entregas/eventos', 'view' => 'pages/generic', 'title' => 'Eventos de Entrega', 'breadcrumbs' => ['Entregas', 'Eventos de Entrega'], 'table' => true, 'filters' => ['Período', 'Status', 'Equipe'], 'stub' => 'SPRINT-06 eventos listagem'],
    ['uri' => '/entregas/eventos/novo', 'view' => 'pages/generic', 'title' => 'Criar Evento de Entrega', 'breadcrumbs' => ['Entregas', 'Criar Evento de Entrega'], 'stub' => 'SPRINT-06 criação de evento'],
    ['uri' => '/entregas/eventos/{id}', 'view' => 'pages/generic', 'title' => 'Detalhe do Evento de Entrega', 'breadcrumbs' => ['Entregas', 'Detalhe do Evento de Entrega'], 'stub' => 'Compat route (plano interno)'],
    ['uri' => '/entregas/eventos/{id}/convidados', 'view' => 'pages/generic', 'title' => 'Convidados do Evento de Entrega', 'breadcrumbs' => ['Entregas', 'Convidados'], 'table' => true, 'filters' => ['Família', 'Código retirada', 'Status'], 'stub' => 'SPRINT-06 convites'],
    ['uri' => '/entregas/eventos/{id}/criancas', 'view' => 'pages/generic', 'title' => 'Crianças do Evento de Entrega', 'breadcrumbs' => ['Entregas', 'Crianças do Evento'], 'table' => true, 'filters' => ['Nome', 'Faixa etária'], 'stub' => 'SPRINT-06 crianças no evento'],

    ['uri' => '/equipamentos', 'view' => 'pages/generic', 'title' => 'Lista de Equipamentos', 'breadcrumbs' => ['Equipamentos', 'Lista'], 'table' => true, 'filters' => ['Nome', 'Status', 'Categoria'], 'stub' => 'SPRINT-08 equipamentos listagem'],
    ['uri' => '/equipamentos/novo', 'view' => 'pages/generic', 'title' => 'Novo Equipamento', 'breadcrumbs' => ['Equipamentos', 'Novo Equipamento'], 'stub' => 'SPRINT-08 equipamentos cadastro'],
    ['uri' => '/equipamentos/{id}', 'view' => 'pages/generic', 'title' => 'Detalhe do Equipamento', 'breadcrumbs' => ['Equipamentos', 'Detalhe do Equipamento'], 'stub' => 'SPRINT-08 detalhe equipamento'],
    ['uri' => '/equipamentos/emprestimos', 'view' => 'pages/generic', 'title' => 'Empréstimos de Equipamentos', 'breadcrumbs' => ['Equipamentos', 'Empréstimos'], 'table' => true, 'filters' => ['Status', 'Data'], 'stub' => 'SPRINT-08 empréstimos'],

    ['uri' => '/relatorios', 'view' => 'pages/generic', 'title' => 'Relatórios', 'breadcrumbs' => ['Relatórios'], 'table' => true, 'filters' => ['Período', 'Módulo', 'Formato'], 'stub' => 'Compat route cliente'],
    ['uri' => '/relatorios/mensais', 'view' => 'pages/generic', 'title' => 'Relatórios Mensais', 'breadcrumbs' => ['Relatórios', 'Relatórios Mensais'], 'table' => true, 'filters' => ['Ano', 'Mês', 'Tipo'], 'stub' => 'SPRINT-09 relatórios gerenciais'],

    ['uri' => '/admin/usuarios', 'view' => 'pages/generic', 'title' => 'Lista de Usuários', 'breadcrumbs' => ['Administração', 'Usuários'], 'table' => true, 'filters' => ['Nome', 'Perfil', 'Status'], 'admin_only' => true, 'stub' => 'SPRINT-03 gestão usuários'],
    ['uri' => '/admin/configuracoes', 'view' => 'pages/generic', 'title' => 'Configurações', 'breadcrumbs' => ['Administração', 'Configurações'], 'admin_only' => true, 'stub' => 'Compat route cliente'],
    ['uri' => '/admin/config', 'view' => 'pages/generic', 'title' => 'Configurações', 'breadcrumbs' => ['Administração', 'Configurações'], 'admin_only' => true, 'stub' => 'SPRINT-09 parâmetros'],
];
