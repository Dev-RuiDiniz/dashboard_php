<?php

declare(strict_types=1);

function assertTrue(bool $condition, string $message): void
{
    if (!$condition) {
        fwrite(STDERR, 'Assertion failed: ' . $message . PHP_EOL);
        exit(1);
    }
}

$output = shell_exec('php scripts/handover_closure_report.php');
assertTrue(is_string($output), 'script deve retornar output');

$decoded = json_decode($output ?: '{}', true);
assertTrue(is_array($decoded), 'output deve ser json válido');
assertTrue(isset($decoded['checks']) && is_array($decoded['checks']), 'deve conter checks');
assertTrue(isset($decoded['handover_ready']), 'deve conter handover_ready');

$hasOpenApi = false;
foreach (($decoded['checks'] ?? []) as $check) {
    if (($check['artifact'] ?? '') === 'docs/sprints/artifacts/openapi_php_v1.json' && !empty($check['exists'])) {
        $hasOpenApi = true;
    }
}
assertTrue($hasOpenApi, 'openapi v1 deve existir');

echo 'OK: HandoverClosureReportTest' . PHP_EOL;
