<?php

declare(strict_types=1);

function assertTrue(bool $condition, string $message): void
{
    if (!$condition) {
        fwrite(STDERR, 'Assertion failed: ' . $message . PHP_EOL);
        exit(1);
    }
}

$dir = '/tmp/pilot_cutover_dry_run_test';
if (!is_dir($dir)) {
    mkdir($dir, 0777, true);
}

file_put_contents($dir . '/security_posture.json', json_encode([
    'summary' => [
        'posture' => 'baseline_ok',
    ],
], JSON_PRETTY_PRINT));

file_put_contents($dir . '/reconciliation_report.json', json_encode([
    'domains' => [
        'social' => ['families_total' => 1],
    ],
], JSON_PRETTY_PRINT));

$output = shell_exec('php scripts/pilot_cutover_dry_run.php --input-dir ' . escapeshellarg($dir));
assertTrue(is_string($output), 'script deve retornar output');

$decoded = json_decode($output ?: '{}', true);
assertTrue(is_array($decoded), 'output deve ser json válido');
assertTrue(($decoded['decision'] ?? '') === 'GO', 'decisão deve ser GO para cenário válido');
assertTrue(empty($decoded['failed_checks'] ?? []), 'não deve haver checks falhos');

array_map('unlink', glob($dir . '/*.json') ?: []);
rmdir($dir);

echo 'OK: PilotCutoverDryRunTest' . PHP_EOL;
