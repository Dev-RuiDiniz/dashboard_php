<?php

declare(strict_types=1);

require_once __DIR__ . '/../../src/Domain/AuthResetTokenStore.php';

use App\Domain\AuthResetTokenStore;

function assertTrue(bool $condition, string $message): void
{
    if (!$condition) {
        fwrite(STDERR, "Assertion failed: {$message}" . PHP_EOL);
        exit(1);
    }
}

$tmpReset = sys_get_temp_dir() . '/auth_reset_store_' . uniqid('', true) . '.json';
$store = new AuthResetTokenStore($tmpReset);

$now = 1710000000;
$token = $store->issueToken('admin@local', $now + 3600, $now);
assertTrue($token !== '', 'issueToken deve retornar token não vazio');

$raw = file_get_contents($tmpReset);
assertTrue(is_string($raw) && $raw !== '', 'arquivo de storage deve ser criado');
assertTrue(strpos($raw, $token) === false, 'token plaintext não deve ser persistido em disco');

$email = $store->consumeToken($token, $now + 10);
assertTrue($email === 'admin@local', 'consumeToken deve retornar email válido para token ativo');

$reuse = $store->consumeToken($token, $now + 20);
assertTrue($reuse === null, 'token deve ser de uso único');

$expiredToken = $store->issueToken('admin@local', $now - 1, $now - 100);
$expired = $store->consumeToken($expiredToken, $now);
assertTrue($expired === null, 'token expirado deve ser rejeitado');

$store->reset();

echo "OK: AuthResetTokenStoreTest" . PHP_EOL;
