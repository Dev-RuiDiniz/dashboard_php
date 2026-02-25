<?php

declare(strict_types=1);

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
require_once __DIR__ . '/../../src/Reports/ExportService.php';
require_once __DIR__ . '/../../src/Http/Kernel.php';

use App\Domain\AuthThrottleStore;
use App\Domain\DeliveryStore;
use App\Domain\EquipmentStore;
use App\Domain\SettingsStore;
use App\Domain\SocialStore;
use App\Domain\StreetStore;
use App\Http\Kernel;

function assertTrue(bool $condition, string $message): void
{
    if (!$condition) {
        fwrite(STDERR, "Assertion failed: {$message}" . PHP_EOL);
        exit(1);
    }
}

$social = new SocialStore('/tmp/social_store_test_s10.json');
$street = new StreetStore('/tmp/street_store_test_s10.json');
$delivery = new DeliveryStore('/tmp/delivery_store_test_s10.json');
$equipment = new EquipmentStore('/tmp/equipment_store_test_s10.json');
$settings = new SettingsStore('/tmp/settings_store_test_s10.json');
$throttle = new AuthThrottleStore('/tmp/auth_throttle_test_s10.json');
$social->reset(); $street->reset(); $delivery->reset(); $equipment->reset(); $settings->reset(); $throttle->reset();
$kernel = new Kernel(socialStore:$social, streetStore:$street, deliveryStore:$delivery, equipmentStore:$equipment, settingsStore:$settings, authThrottleStore:$throttle);
$env=['JWT_SECRET'=>'test-secret'];

for ($i = 1; $i <= 5; $i++) {
    $r = $kernel->handle('POST', '/auth/login', 'req-fail-' . $i, [], ['email'=>'admin@local','password'=>'wrong'], $env);
}
assertTrue(($r['status'] ?? 0) === 429, 'apos tentativas falhas deve bloquear com 429');

$blocked = $kernel->handle('POST', '/auth/login', 'req-fail-6', [], ['email'=>'admin@local','password'=>'admin123'], $env);
assertTrue(($blocked['status'] ?? 0) === 429, 'login correto ainda bloqueado durante lockout');

$throttle->reset();
$ok = $kernel->handle('POST', '/auth/login', 'req-ok', [], ['email'=>'admin@local','password'=>'admin123'], $env);
assertTrue(($ok['status'] ?? 0) === 200, 'apos reset lockout login deve funcionar');

$social->reset(); $street->reset(); $delivery->reset(); $equipment->reset(); $settings->reset(); $throttle->reset();
echo "OK: SecurityHardeningTest" . PHP_EOL;
