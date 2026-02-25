<?php

declare(strict_types=1);

function assertTrue(bool $condition, string $message): void
{
    if (!$condition) {
        fwrite(STDERR, 'Assertion failed: ' . $message . PHP_EOL);
        exit(1);
    }
}

$dir = '/tmp/reconciliation_report_test_data';
if (!is_dir($dir)) {
    mkdir($dir, 0777, true);
}

file_put_contents($dir . '/social_store.json', json_encode([
    'families' => ['1' => ['id' => 1]],
    'dependents' => ['1' => ['id' => 1]],
    'children' => [],
], JSON_PRETTY_PRINT));

file_put_contents($dir . '/street_store.json', json_encode([
    'people' => ['1' => ['id' => 1]],
    'referrals' => ['1' => ['id' => 1]],
], JSON_PRETTY_PRINT));

file_put_contents($dir . '/delivery_store.json', json_encode([
    'events' => ['1' => ['id' => 1]],
    'invites' => [],
    'withdrawals' => [],
], JSON_PRETTY_PRINT));

file_put_contents($dir . '/equipment_store.json', json_encode([
    'equipments' => ['1' => ['id' => 1]],
    'loans' => [],
], JSON_PRETTY_PRINT));

file_put_contents($dir . '/settings_store.json', json_encode([
    'max_deliveries_per_month' => 1,
], JSON_PRETTY_PRINT));

$output = shell_exec('php scripts/reconciliation_report.php --data-dir ' . escapeshellarg($dir));
assertTrue(is_string($output), 'script deve retornar output');
$decoded = json_decode($output ?: '{}', true);
assertTrue(is_array($decoded), 'output deve ser json válido');
assertTrue((int) ($decoded['domains']['social']['families_total'] ?? 0) === 1, 'deve contar famílias');
assertTrue((int) ($decoded['domains']['street']['people_total'] ?? 0) === 1, 'deve contar pessoas street');
assertTrue((int) ($decoded['domains']['delivery']['events_total'] ?? 0) === 1, 'deve contar eventos');
assertTrue((int) ($decoded['domains']['equipment']['equipments_total'] ?? 0) === 1, 'deve contar equipamentos');
assertTrue((bool) ($decoded['domains']['settings']['has_settings'] ?? false) === true, 'deve detectar settings');

array_map('unlink', glob($dir . '/*.json') ?: []);
rmdir($dir);

echo 'OK: ReconciliationReportTest' . PHP_EOL;
