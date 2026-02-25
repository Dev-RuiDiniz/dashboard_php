<?php

declare(strict_types=1);

require_once __DIR__ . '/../../src/Domain/SocialStore.php';

use App\Domain\SocialStore;

function assertTrue(bool $condition, string $message): void
{
    if (!$condition) {
        fwrite(STDERR, 'Assertion failed: ' . $message . PHP_EOL);
        exit(1);
    }
}

$migrationFile = __DIR__ . '/../../database/migrations/001_create_social_core.sql';
assertTrue(file_exists($migrationFile), 'migration SQL da sprint 11 deve existir');

$sql = strtolower((string) file_get_contents($migrationFile));
assertTrue(str_contains($sql, 'create table if not exists families'), 'migration deve criar tabela families');
assertTrue(str_contains($sql, 'create table if not exists dependents'), 'migration deve criar tabela dependents');
assertTrue(str_contains($sql, 'create table if not exists children'), 'migration deve criar tabela children');
assertTrue(str_contains($sql, 'unique (responsible_cpf)'), 'migration deve ter unique de cpf');

putenv('SOCIAL_STORE_DRIVER=json');
$store = new SocialStore('/tmp/social_store_relational_readiness_test.json');
$store->reset();

$family = $store->createFamily('Teste Persistencia', '52998224725');
assertTrue((int) ($family['id'] ?? 0) > 0, 'deve criar família no modo json fallback');
assertTrue($store->familyCpfExists('52998224725'), 'familyCpfExists deve funcionar no fallback json');

$store->reset();

echo 'OK: RelationalMigrationReadinessTest' . PHP_EOL;
