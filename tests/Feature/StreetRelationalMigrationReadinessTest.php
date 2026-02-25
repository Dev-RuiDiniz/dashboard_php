<?php

declare(strict_types=1);

require_once __DIR__ . '/../../src/Domain/StreetStore.php';

use App\Domain\StreetStore;

function assertTrue(bool $condition, string $message): void
{
    if (!$condition) {
        fwrite(STDERR, 'Assertion failed: ' . $message . PHP_EOL);
        exit(1);
    }
}

$migrationFile = __DIR__ . '/../../database/migrations/002_create_street_core.sql';
assertTrue(file_exists($migrationFile), 'migration SQL da sprint 12 deve existir');

$sql = strtolower((string) file_get_contents($migrationFile));
assertTrue(str_contains($sql, 'create table if not exists street_residents'), 'migration deve criar tabela street_residents');
assertTrue(str_contains($sql, 'create table if not exists street_referrals'), 'migration deve criar tabela street_referrals');
assertTrue(str_contains($sql, 'foreign key (street_resident_id)'), 'migration deve conter fk para street_residents');

putenv('STREET_STORE_DRIVER=json');
$store = new StreetStore('/tmp/street_store_relational_readiness_test.json');
$store->reset();

$person = $store->createPerson('Pessoa Rua', false, false, '');
assertTrue((int) ($person['id'] ?? 0) > 0, 'deve criar pessoa no modo json fallback');

$referral = $store->createReferral((int) $person['id'], 'CRAS');
assertTrue(is_array($referral), 'deve criar encaminhamento no fallback json');

$store->reset();

echo 'OK: StreetRelationalMigrationReadinessTest' . PHP_EOL;
