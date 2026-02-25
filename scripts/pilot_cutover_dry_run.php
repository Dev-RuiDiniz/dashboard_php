<?php

declare(strict_types=1);

$options = $_SERVER['argv'] ?? [];
$inputDir = __DIR__ . '/../tmp';

for ($i = 1; $i < count($options); $i++) {
    if ($options[$i] === '--input-dir' && isset($options[$i + 1])) {
        $inputDir = (string) $options[$i + 1];
        $i++;
    }
}

/** @return array<string,mixed> */
function readJson(string $file): array
{
    if (!file_exists($file)) {
        return [];
    }
    $raw = file_get_contents($file);
    $decoded = json_decode($raw ?: '{}', true);
    return is_array($decoded) ? $decoded : [];
}

$security = readJson($inputDir . '/security_posture.json');
$reconciliation = readJson($inputDir . '/reconciliation_report.json');

$checks = [
    'security_posture_available' => !empty($security),
    'reconciliation_available' => !empty($reconciliation),
    'security_baseline_ok' => (($security['summary']['posture'] ?? '') === 'baseline_ok'),
    'social_has_data' => ((int) ($reconciliation['domains']['social']['families_total'] ?? 0) >= 0),
];

$failed = [];
foreach ($checks as $key => $ok) {
    if (!$ok) {
        $failed[] = $key;
    }
}

$go = count($failed) === 0;

$out = [
    'generated_at' => gmdate('c'),
    'input_dir' => realpath($inputDir) ?: $inputDir,
    'checks' => $checks,
    'decision' => $go ? 'GO' : 'NO_GO',
    'failed_checks' => $failed,
    'notes' => $go
        ? 'Janela piloto apta para execução controlada.'
        : 'Pré-condições insuficientes para janela piloto.',
];

echo json_encode($out, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT) . PHP_EOL;
