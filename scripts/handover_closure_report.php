<?php

declare(strict_types=1);

$requiredArtifacts = [
    'docs/sprints/SPRINT_16_RUNBOOK.md',
    'docs/sprints/SPRINT_19_REPORT.md',
    'docs/sprints/artifacts/openapi_php_v1.json',
    'docs/sprints/artifacts/golden_exports/families.csv',
];

$root = realpath(__DIR__ . '/..') ?: dirname(__DIR__);
$checks = [];
foreach ($requiredArtifacts as $relative) {
    $full = $root . '/' . $relative;
    $checks[] = [
        'artifact' => $relative,
        'exists' => file_exists($full),
    ];
}

$missing = [];
foreach ($checks as $check) {
    if (!$check['exists']) {
        $missing[] = $check['artifact'];
    }
}

$report = [
    'generated_at' => gmdate('c'),
    'checks' => $checks,
    'handover_ready' => count($missing) === 0,
    'missing_artifacts' => $missing,
    'next_action' => count($missing) === 0
        ? 'Preparar assinatura formal de encerramento e handover operacional.'
        : 'Completar artefatos ausentes antes do encerramento formal.',
];

echo json_encode($report, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT) . PHP_EOL;
