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

$social = new SocialStore('/tmp/social_store_test_s27_monthly.json');
$street = new StreetStore('/tmp/street_store_test_s27_monthly.json');
$delivery = new DeliveryStore('/tmp/delivery_store_test_s27_monthly.json');
$equipment = new EquipmentStore('/tmp/equipment_store_test_s27_monthly.json');
$settings = new SettingsStore('/tmp/settings_store_test_s27_monthly.json');
$social->reset(); $street->reset(); $delivery->reset(); $equipment->reset(); $settings->reset();
$kernel = new Kernel(socialStore: $social, streetStore: $street, deliveryStore: $delivery, equipmentStore: $equipment, settingsStore: $settings);
$env = ['JWT_SECRET' => 'test-secret'];

$login = $kernel->handle('POST', '/auth/login', 'req-login', [], ['email' => 'operador@local', 'password' => 'operador123'], $env);
$h = ['Authorization' => 'Bearer ' . (string) ($login['body']['access_token'] ?? '')];

$fam = $kernel->handle('POST', '/families', 'req-f1', $h, ['responsible_full_name' => 'Fam 1', 'responsible_cpf' => '529.982.247-25'], $env);
$familyId = (int) ($fam['body']['item']['id'] ?? 0);

$kernel->handle('POST', '/visits', 'req-v1', $h, ['person_id' => 10, 'family_id' => $familyId, 'scheduled_for' => '2026-03-10 09:00:00', 'notes' => 'pendente'], $env);
$v2 = $kernel->handle('POST', '/visits', 'req-v2', $h, ['person_id' => 11, 'family_id' => $familyId, 'scheduled_for' => '2026-03-12 10:00:00', 'notes' => 'a concluir'], $env);
$visitId2 = (int) ($v2['body']['item']['id'] ?? 0);
$kernel->handle('POST', '/visits/' . $visitId2 . '/complete', 'req-v2-complete', $h, ['completed_at' => '2026-03-12 11:00:00'], $env);

$e = $kernel->handle('POST', '/deliveries/events', 'req-e1', $h, ['name' => 'Evento Março', 'event_date' => '2026-03-20'], $env);
$eventId = (int) ($e['body']['item']['id'] ?? 0);
$kernel->handle('POST', '/deliveries/events/' . $eventId . '/publish', 'req-e1-publish', $h, ['published_at' => '2026-03-19 08:00:00'], $env);

$monthly = $kernel->handle('GET', '/reports/monthly', 'req-monthly', $h, ['period' => '2026-03'], $env);
assertTrue(($monthly['status'] ?? 0) === 200, 'monthly deve retornar 200');
assertTrue((string) ($monthly['body']['period'] ?? '') === '2026-03', 'periodo deve ser retornado');
$summary = (array) ($monthly['body']['summary'] ?? []);
assertTrue((int) ($summary['delivery_events_total'] ?? 0) >= 1, 'monthly deve contabilizar eventos do periodo');
assertTrue((int) ($summary['delivery_events_published_total'] ?? 0) >= 1, 'monthly deve contabilizar eventos publicados');
assertTrue((int) ($summary['visits_total'] ?? 0) >= 2, 'monthly deve contabilizar visitas do periodo');
assertTrue((int) (($summary['visits_by_status']['concluida'] ?? 0)) >= 1, 'monthly deve contabilizar visitas concluidas');

$invalid = $kernel->handle('GET', '/reports/monthly', 'req-monthly-invalid', $h, ['period' => '03-2026'], $env);
assertTrue(($invalid['status'] ?? 0) === 422, 'periodo invalido deve retornar 422');

$social->reset(); $street->reset(); $delivery->reset(); $equipment->reset(); $settings->reset();
echo "OK: ReportsMonthlyOperationalTest" . PHP_EOL;
