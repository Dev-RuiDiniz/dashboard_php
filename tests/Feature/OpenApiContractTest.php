<?php

declare(strict_types=1);

function assertTrue(bool $condition, string $message): void
{
    if (!$condition) {
        fwrite(STDERR, 'Assertion failed: ' . $message . PHP_EOL);
        exit(1);
    }
}

$specFile = __DIR__ . '/../../docs/sprints/artifacts/openapi_php_v1.json';
assertTrue(file_exists($specFile), 'openapi_php_v1.json deve existir');

$raw = file_get_contents($specFile);
$spec = json_decode($raw ?: '{}', true);
assertTrue(is_array($spec), 'spec deve ser JSON válido');
assertTrue(($spec['openapi'] ?? '') === '3.0.3', 'versão OpenAPI deve ser 3.0.3');

$paths = $spec['paths'] ?? [];
assertTrue(is_array($paths), 'paths deve existir');

$required = [
    '/health' => ['get'],
    '/ready' => ['get'],
    '/auth/login' => ['post'],
    '/me' => ['get'],
    '/families' => ['get', 'post'],
    '/families/{id}' => ['get', 'put', 'delete'],
    '/street/people' => ['get', 'post'],
    '/deliveries/events' => ['get', 'post'],
    '/deliveries/events/{id}/publish' => ['post'],
    '/equipment' => ['get', 'post'],
    '/reports/summary' => ['get'],
    '/reports/monthly' => ['get'],
    '/settings/eligibility' => ['get', 'put'],
    '/eligibility/check' => ['post'],
    '/visits' => ['get', 'post'],
    '/visits/{id}/complete' => ['post'],
];

foreach ($required as $path => $methods) {
    assertTrue(isset($paths[$path]) && is_array($paths[$path]), 'path obrigatório ausente: ' . $path);
    foreach ($methods as $method) {
        assertTrue(isset($paths[$path][$method]), 'método obrigatório ausente: ' . strtoupper($method) . ' ' . $path);
    }
}

echo 'OK: OpenApiContractTest' . PHP_EOL;
