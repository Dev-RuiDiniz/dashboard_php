<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title><?= htmlspecialchars($title ?? 'Dashboard') ?></title>
  <style>
    body { font-family: Arial, sans-serif; margin:0; background:#f8fafc; color:#111827; }
    .app { display:flex; min-height:100vh; }
    .sidebar { width:240px; background:#111827; color:white; padding:16px; }
    .sidebar a { color:#d1d5db; text-decoration:none; display:block; margin:8px 0; }
    .main { flex:1; padding:16px; }
    .topbar { display:flex; gap:8px; align-items:center; justify-content:space-between; }
    .search { flex:1; margin:0 8px; }
    .search input { width:100%; padding:10px; border-radius:8px; border:1px solid #d1d5db; }
    .breadcrumbs { color:#6b7280; font-size:14px; margin:10px 0; }
    .card { background:white; border:1px solid #e5e7eb; border-radius:10px; padding:12px; margin-top:12px; }
    .fab { position:fixed; right:20px; bottom:20px; background:#2563eb; color:white; border-radius:999px; padding:10px 14px; }
    .chips span { display:inline-block; border-radius:999px; padding:4px 8px; background:#fee2e2; margin-right:4px; margin-bottom:4px; font-size:12px; }
    table { width:100%; border-collapse:collapse; }
    th, td { border-bottom:1px solid #e5e7eb; text-align:left; padding:8px; }
    .mobile-menu { display:none; }
    @media (max-width: 960px) {
      .sidebar { display:none; }
      .mobile-menu { display:inline-block; }
      .main { padding:12px; }
      .table-wrap { overflow-x:auto; }
    }
  </style>
</head>
<body>
<div class="app">
  <aside class="sidebar">
    <strong>Menu</strong>
    <a href="/dashboard">Dashboard</a>
    <a href="/familias">Famílias</a>
    <a href="/pessoas">Pessoas</a>
    <a href="/criancas">Crianças</a>
    <a href="/entregas/eventos">Entregas</a>
    <a href="/equipamentos">Equipamentos</a>
    <a href="/relatorios/mensais">Relatórios</a>
    <a href="/admin/usuarios">Usuários/Config</a>
  </aside>
  <main class="main">
    <header class="topbar">
      <button class="mobile-menu">☰</button>
      <div class="search"><input placeholder="Busca global: nome/CPF/RG/família" /></div>
      <span>Perfil: voluntário</span>
    </header>
    <div class="breadcrumbs"><?= htmlspecialchars(implode(' / ', $breadcrumbs ?? ['Início'])) ?></div>
    <?= $content ?>
  </main>
</div>
<div class="fab">Novo: Atendimento • Família • Evento • Equipamento</div>
</body>
</html>
