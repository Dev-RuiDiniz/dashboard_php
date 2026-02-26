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
require_once __DIR__ . '/../../src/Domain/AuthResetTokenStore.php';
require_once __DIR__ . '/../../src/Reports/ExportService.php';
require_once __DIR__ . '/../../src/Http/Kernel.php';

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

$social = new SocialStore('/tmp/social_store_test_s29_binary.json');
$street = new StreetStore('/tmp/street_store_test_s29_binary.json');
$delivery = new DeliveryStore('/tmp/delivery_store_test_s29_binary.json');
$equipment = new EquipmentStore('/tmp/equipment_store_test_s29_binary.json');
$settings = new SettingsStore('/tmp/settings_store_test_s29_binary.json');
$social->reset(); $street->reset(); $delivery->reset(); $equipment->reset(); $settings->reset();
$kernel = new Kernel(socialStore: $social, streetStore: $street, deliveryStore: $delivery, equipmentStore: $equipment, settingsStore: $settings);
$env = ['JWT_SECRET' => 'test-secret'];

$login = $kernel->handle('POST', '/auth/login', 'req-login', [], ['email' => 'operador@local', 'password' => 'operador123'], $env);
$h = ['Authorization' => 'Bearer ' . (string) ($login['body']['access_token'] ?? '')];
$kernel->handle('POST', '/families', 'req-f1', $h, ['responsible_full_name' => 'Fam 1', 'responsible_cpf' => '529.982.247-25'], $env);

$xlsx = $kernel->handle('GET', '/reports/monthly/export.xlsx', 'req-xlsx', $h, ['period' => '2026-04'], $env);
assertTrue(($xlsx['status'] ?? 0) === 200, 'xlsx mensal deve retornar 200');
assertTrue(str_contains((string) ($xlsx['body']['__raw'] ?? ''), '<Workbook'), 'xlsx deve retornar workbook XML');

$pdf = $kernel->handle('GET', '/reports/monthly/export.pdf', 'req-pdf', $h, ['period' => '2026-04'], $env);
assertTrue(($pdf['status'] ?? 0) === 200, 'pdf mensal deve retornar 200');
assertTrue(str_starts_with((string) ($pdf['body']['__raw'] ?? ''), '%PDF-1.4'), 'pdf deve iniciar com assinatura PDF');

$social->reset(); $street->reset(); $delivery->reset(); $equipment->reset(); $settings->reset();
echo "OK: ReportsMonthlyBinaryExportsTest" . PHP_EOL;
