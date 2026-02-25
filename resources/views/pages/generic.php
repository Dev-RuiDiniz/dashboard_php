<section class="card">
  <h1><?= htmlspecialchars($title ?? 'Tela') ?></h1>
  <p><strong>Rota:</strong> <code><?= htmlspecialchars($route ?? '') ?></code></p>
  <p><strong>Status:</strong> Stub inicial integrado ao backend PHP. TODO: <?= htmlspecialchars($stub ?? 'definir sprint') ?>.</p>
</section>

<section class="card">
  <h2>Estados padronizados</h2>
  <ul>
    <li>Loading: carregando dados…</li>
    <li>Vazio: nenhum registro encontrado.</li>
    <li>Erro: não foi possível carregar os dados.</li>
  </ul>
</section>

<?php if (!empty($chips)): ?>
<section class="card">
  <h2>Chips de alerta</h2>
  <div class="chips">
    <?php foreach ($chips as $chip): ?>
      <span><?= htmlspecialchars((string) $chip) ?></span>
    <?php endforeach; ?>
  </div>
</section>
<?php endif; ?>

<?php if (!empty($filters)): ?>
<section class="card">
  <h2>Filtros</h2>
  <p><?= htmlspecialchars(implode(' • ', $filters)) ?></p>
</section>
<?php endif; ?>

<?php if (($table ?? false) === true): ?>
<section class="card">
  <h2>Tabela</h2>
  <div class="table-wrap">
    <table>
      <thead><tr><th>Coluna</th><th>Status</th><th>Ação</th></tr></thead>
      <tbody>
        <tr><td>Exemplo 01</td><td>Stub</td><td>Ver</td></tr>
      </tbody>
    </table>
  </div>
</section>
<?php endif; ?>

<?php if (($timeline ?? false) === true): ?>
<section class="card">
  <h2>Timeline</h2>
  <ol>
    <li>2026-01-01 — Registro inicial</li>
    <li>2026-01-15 — Atualização de atendimento</li>
  </ol>
</section>
<?php endif; ?>
