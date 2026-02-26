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

$social = new SocialStore('/tmp/social_store_test_s28_export.json');
$street = new StreetStore('/tmp/street_store_test_s28_export.json');
$delivery = new DeliveryStore('/tmp/delivery_store_test_s28_export.json');
$equipment = new EquipmentStore('/tmp/equipment_store_test_s28_export.json');
$settings = new SettingsStore('/tmp/settings_store_test_s28_export.json');
$social->reset(); $street->reset(); $delivery->reset(); $equipment->reset(); $settings->reset();
$kernel = new Kernel(socialStore: $social, streetStore: $street, deliveryStore: $delivery, equipmentStore: $equipment, settingsStore: $settings);
$env = ['JWT_SECRET' => 'test-secret'];

$login = $kernel->handle('POST', '/auth/login', 'req-login', [], ['email' => 'operador@local', 'password' => 'operador123'], $env);
$h = ['Authorization' => 'Bearer ' . (string) ($login['body']['access_token'] ?? '')];

$fam = $kernel->handle('POST', '/families', 'req-f1', $h, ['responsible_full_name' => 'Fam 1', 'responsible_cpf' => '529.982.247-25'], $env);
$familyId = (int) ($fam['body']['item']['id'] ?? 0);
$kernel->handle('POST', '/visits', 'req-v1', $h, ['person_id' => 30, 'family_id' => $familyId, 'scheduled_for' => '2026-04-05 09:30:00', 'notes' => 'visita'], $env);

$monthlyCsv = $kernel->handle('GET', '/reports/monthly/export.csv', 'req-monthly-csv', $h, ['period' => '2026-04', 'visit_status' => 'pendente'], $env);
assertTrue(($monthlyCsv['status'] ?? 0) === 200, 'export csv mensal deve retornar 200');
$raw = (string) ($monthlyCsv['body']['__raw'] ?? '');
assertTrue(str_contains($raw, '"period","metric","value"'), 'csv deve conter cabecalho');
assertTrue(str_contains($raw, '"2026-04","visits_total"'), 'csv deve conter visits_total do periodo');

$invalid = $kernel->handle('GET', '/reports/monthly/export.csv', 'req-monthly-csv-invalid', $h, ['period' => '2026/04'], $env);
assertTrue(($invalid['status'] ?? 0) === 422, 'periodo invalido deve retornar 422');

$social->reset(); $street->reset(); $delivery->reset(); $equipment->reset(); $settings->reset();
echo "OK: ReportsMonthlyExportTest" . PHP_EOL;
