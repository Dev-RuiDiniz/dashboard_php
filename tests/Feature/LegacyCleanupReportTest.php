<?php

declare(strict_types=1);

function assertTrue(bool $condition, string $message): void
{
    if (!$condition) {
        fwrite(STDERR, 'Assertion failed: ' . $message . PHP_EOL);
        exit(1);
    }
}

$output = shell_exec('php scripts/legacy_cleanup_report.php');
assertTrue(is_string($output), 'script deve gerar saída');

$decoded = json_decode($output ?: '{}', true);
assertTrue(is_array($decoded), 'saída deve ser json válido');
assertTrue(isset($decoded['policy']) && is_array($decoded['policy']), 'deve conter política');
assertTrue(isset($decoded['inventory']) && is_array($decoded['inventory']), 'deve conter inventário');

$hasLegacyPath = false;
foreach (($decoded['inventory'] ?? []) as $item) {
    if (($item['path'] ?? '') === 'frontend/legacy') {
        $hasLegacyPath = true;
    }
}
assertTrue($hasLegacyPath, 'inventário deve incluir frontend/legacy');

echo 'OK: LegacyCleanupReportTest' . PHP_EOL;
