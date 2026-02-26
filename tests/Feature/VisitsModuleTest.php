<?php

declare(strict_types=1);

require_once __DIR__ . '/../../src/Http/Kernel.php';
require_once __DIR__ . '/../../src/Auth/JwtService.php';
require_once __DIR__ . '/../../src/Auth/UserStore.php';
require_once __DIR__ . '/../../src/Domain/CpfValidator.php';
require_once __DIR__ . '/../../src/Domain/SocialStore.php';
require_once __DIR__ . '/../../src/Domain/StreetStore.php';
require_once __DIR__ . '/../../src/Domain/DeliveryStore.php';
require_once __DIR__ . '/../../src/Domain/EquipmentStore.php';
require_once __DIR__ . '/../../src/Domain/SettingsStore.php';
require_once __DIR__ . '/../../src/Domain/EligibilityService.php';
require_once __DIR__ . '/../../src/Domain/AuthThrottleStore.php';
require_once __DIR__ . '/../../src/Domain/AuthResetTokenStore.php';
require_once __DIR__ . '/../../src/Reports/ExportService.php';

use App\Http\Kernel;

function assertTrue(bool $condition, string $message): void
{
    if (!$condition) {
        fwrite(STDERR, "Assertion failed: {$message}" . PHP_EOL);
        exit(1);
    }
}

$kernel = new Kernel();
$env = ['JWT_SECRET' => 'test-secret'];

$opLogin = $kernel->handle('POST', '/auth/login', 'req-op', [], ['email' => 'operador@local', 'password' => 'operador123'], $env);
$opToken = (string) ($opLogin['body']['access_token'] ?? '');

$create = $kernel->handle('POST', '/visits', 'req-create', ['Authorization' => 'Bearer ' . $opToken], [
    'person_id' => 1001,
    'family_id' => 1,
    'scheduled_for' => '2026-01-10 14:00:00',
    'notes' => 'Primeira visita',
], $env);
assertTrue(($create['status'] ?? 0) === 201, 'operador deve criar visita');
$visitId = (int) ($create['body']['item']['id'] ?? 0);
assertTrue($visitId > 0, 'id da visita deve ser retornado');

$listPending = $kernel->handle('GET', '/visits', 'req-list-pending', ['Authorization' => 'Bearer ' . $opToken], ['status' => 'pendente'], $env);
assertTrue(($listPending['status'] ?? 0) === 200, 'listar visitas pendentes deve funcionar');
assertTrue(count((array) ($listPending['body']['items'] ?? [])) >= 1, 'deve ter ao menos uma visita pendente');

$complete = $kernel->handle('POST', '/visits/' . $visitId . '/complete', 'req-complete', ['Authorization' => 'Bearer ' . $opToken], ['completed_at' => '2026-01-10 15:00:00'], $env);
assertTrue(($complete['status'] ?? 0) === 200, 'deve concluir visita existente');
assertTrue((string) ($complete['body']['item']['status'] ?? '') === 'concluida', 'status deve ser concluida');

$readLogin = $kernel->handle('POST', '/auth/login', 'req-read', [], ['email' => 'leitura@local', 'password' => 'leitura123'], $env);
$readToken = (string) ($readLogin['body']['access_token'] ?? '');
$readList = $kernel->handle('GET', '/visits', 'req-read-list', ['Authorization' => 'Bearer ' . $readToken], [], $env);
assertTrue(($readList['status'] ?? 0) === 200, 'viewer deve ler visitas');
$readWriteDenied = $kernel->handle('POST', '/visits', 'req-read-write', ['Authorization' => 'Bearer ' . $readToken], ['person_id' => 2, 'scheduled_for' => '2026-01-10 10:00:00'], $env);
assertTrue(($readWriteDenied['status'] ?? 0) === 403, 'viewer não deve criar visita');

echo "OK: VisitsModuleTest" . PHP_EOL;
