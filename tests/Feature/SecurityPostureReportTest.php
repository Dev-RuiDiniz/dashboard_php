<?php

declare(strict_types=1);

function assertTrue(bool $condition, string $message): void
{
    if (!$condition) {
        fwrite(STDERR, 'Assertion failed: ' . $message . PHP_EOL);
        exit(1);
    }
}

putenv('JWT_SECRET=test-secret');
putenv('MYSQL_HOST=127.0.0.1');

$output = shell_exec('php scripts/security_posture_report.php');
assertTrue(is_string($output), 'script de postura deve retornar output');

$decoded = json_decode($output ?: '{}', true);
assertTrue(is_array($decoded), 'output deve ser json valido');
assertTrue(isset($decoded['checks']['files']) && is_array($decoded['checks']['files']), 'deve conter checks de arquivos');
assertTrue(isset($decoded['checks']['env']) && is_array($decoded['checks']['env']), 'deve conter checks de env');
assertTrue(isset($decoded['summary']['posture']), 'deve conter resumo de postura');

$hasJwt = false;
foreach (($decoded['checks']['env'] ?? []) as $envCheck) {
    if (($envCheck['key'] ?? '') === 'JWT_SECRET' && !empty($envCheck['is_set'])) {
        $hasJwt = true;
    }
}
assertTrue($hasJwt, 'JWT_SECRET deve aparecer como setado no teste');

echo 'OK: SecurityPostureReportTest' . PHP_EOL;
