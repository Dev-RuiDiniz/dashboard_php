<?php

declare(strict_types=1);

require_once __DIR__ . '/../../src/Auth/JwtService.php';
require_once __DIR__ . '/../../src/Auth/UserStore.php';
require_once __DIR__ . '/../../src/Domain/CpfValidator.php';
require_once __DIR__ . '/../../src/Domain/SocialStore.php';
require_once __DIR__ . '/../../src/Domain/StreetStore.php';
require_once __DIR__ . '/../../src/Domain/DeliveryStore.php';
require_once __DIR__ . '/../../src/Http/Kernel.php';

use App\Http\Kernel;

function assertTrue(bool $condition, string $message): void
{
    if (!$condition) {
        fwrite(STDERR, "Assertion failed: {$message}" . PHP_EOL);
        exit(1);
    }
}

$kernel = new Kernel();

$health = $kernel->handle('GET', '/health', 'req-1', [], [], []);
assertTrue($health['status'] === 200, 'health status must be 200');
assertTrue(($health['body']['status'] ?? '') === 'ok', 'health body status must be ok');

$ready = $kernel->handle('GET', '/ready', 'req-2', [], [], ['APP_READY' => 'true']);
assertTrue($ready['status'] === 200, 'ready status must be 200 when APP_READY=true');
assertTrue(($ready['body']['status'] ?? '') === 'ready', 'ready body status must be ready');

$notReady = $kernel->handle('GET', '/ready', 'req-3', [], [], ['APP_READY' => 'false']);
assertTrue($notReady['status'] === 503, 'ready status must be 503 when APP_READY=false');
assertTrue(($notReady['body']['status'] ?? '') === 'not_ready', 'ready body status must be not_ready');

$notFound = $kernel->handle('GET', '/unknown', 'req-4', [], [], []);
assertTrue($notFound['status'] === 404, 'unknown route must return 404');
assertTrue(($notFound['body']['request_id'] ?? '') === 'req-4', 'request_id must be propagated in response');

echo "OK: HealthReadyTest" . PHP_EOL;
