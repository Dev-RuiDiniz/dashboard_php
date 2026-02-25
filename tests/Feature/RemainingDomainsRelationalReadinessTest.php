<?php

declare(strict_types=1);

require_once __DIR__ . '/../../src/Domain/DeliveryStore.php';
require_once __DIR__ . '/../../src/Domain/EquipmentStore.php';
require_once __DIR__ . '/../../src/Domain/SettingsStore.php';

use App\Domain\DeliveryStore;
use App\Domain\EquipmentStore;
use App\Domain\SettingsStore;

function assertTrue(bool $condition, string $message): void
{
    if (!$condition) {
        fwrite(STDERR, 'Assertion failed: ' . $message . PHP_EOL);
        exit(1);
    }
}

$migrationFile = __DIR__ . '/../../database/migrations/003_create_delivery_equipment_settings_core.sql';
assertTrue(file_exists($migrationFile), 'migration SQL da sprint 13 deve existir');

$sql = strtolower((string) file_get_contents($migrationFile));
assertTrue(str_contains($sql, 'create table if not exists delivery_events'), 'migration deve criar delivery_events');
assertTrue(str_contains($sql, 'create table if not exists equipments'), 'migration deve criar equipments');
assertTrue(str_contains($sql, 'create table if not exists eligibility_settings'), 'migration deve criar eligibility_settings');

putenv('DELIVERY_STORE_DRIVER=json');
putenv('EQUIPMENT_STORE_DRIVER=json');
putenv('SETTINGS_STORE_DRIVER=json');

$delivery = new DeliveryStore('/tmp/delivery_store_relational_readiness_test.json');
$equipment = new EquipmentStore('/tmp/equipment_store_relational_readiness_test.json');
$settings = new SettingsStore('/tmp/settings_store_relational_readiness_test.json');

$delivery->reset();
$equipment->reset();
$settings->reset();

$event = $delivery->createEvent('Evento Teste', '2026-01-01');
assertTrue((int) ($event['id'] ?? 0) > 0, 'deve criar evento no fallback json');

$item = $equipment->createEquipment('cadeira', 'boa', 'ok');
assertTrue((int) ($item['id'] ?? 0) > 0, 'deve criar equipamento no fallback json');

$updated = $settings->update(['min_vulnerability_score' => 3]);
assertTrue((int) ($updated['min_vulnerability_score'] ?? 0) === 3, 'deve atualizar settings no fallback json');

$delivery->reset();
$equipment->reset();
$settings->reset();

echo 'OK: RemainingDomainsRelationalReadinessTest' . PHP_EOL;
