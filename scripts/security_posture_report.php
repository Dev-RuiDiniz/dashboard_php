<?php

declare(strict_types=1);

$requiredFiles = [
    __DIR__ . '/../.github/workflows/php-ci.yml',
    __DIR__ . '/../docs/sprints/artifacts/openapi_php_v1.json',
    __DIR__ . '/../docs/sprints/SPRINT_16_RUNBOOK.md',
];

$requiredEnv = [
    'JWT_SECRET',
    'MYSQL_HOST',
    'MYSQL_DATABASE',
    'MYSQL_USER',
];

$fileChecks = [];
foreach ($requiredFiles as $file) {
    $fileChecks[] = [
        'file' => str_replace(realpath(__DIR__ . '/..') ?: dirname(__DIR__), '.', $file),
        'exists' => file_exists($file),
    ];
}

$envChecks = [];
foreach ($requiredEnv as $envKey) {
    $value = getenv($envKey);
    $envChecks[] = [
        'key' => $envKey,
        'is_set' => is_string($value) && trim($value) !== '',
    ];
}

$allFilesOk = true;
foreach ($fileChecks as $check) {
    if (!$check['exists']) {
        $allFilesOk = false;
        break;
    }
}

$envSetCount = 0;
foreach ($envChecks as $check) {
    if ($check['is_set']) {
        $envSetCount++;
    }
}

$report = [
    'generated_at' => gmdate('c'),
    'checks' => [
        'files' => $fileChecks,
        'env' => $envChecks,
    ],
    'summary' => [
        'files_ok' => $allFilesOk,
        'env_set_ratio' => sprintf('%d/%d', $envSetCount, count($requiredEnv)),
        'posture' => $allFilesOk ? ($envSetCount >= 2 ? 'baseline_ok' : 'warning_env') : 'fail_missing_files',
    ],
];

echo json_encode($report, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT) . PHP_EOL;
