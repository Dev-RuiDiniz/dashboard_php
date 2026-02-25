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

use App\Auth\JwtService;
use App\Auth\UserStore;
use App\Http\Kernel;
use App\Domain\AuthThrottleStore;
use App\Domain\AuthResetTokenStore;

function assertTrue(bool $condition, string $message): void
{
    if (!$condition) {
        fwrite(STDERR, "Assertion failed: {$message}" . PHP_EOL);
        exit(1);
    }
}

$store = new UserStore();
$admin = $store->findByEmail('admin@local');
assertTrue(is_array($admin), 'admin deve existir');
assertTrue(!isset($admin['password']), 'nao deve existir senha plaintext no cadastro bootstrap');
assertTrue(isset($admin['password_hash']), 'deve existir password_hash no cadastro bootstrap');

$tmpThrottle = sys_get_temp_dir() . '/auth_throttle_' . uniqid('', true) . '.json';
$tmpReset = sys_get_temp_dir() . '/auth_reset_' . uniqid('', true) . '.json';
$throttleStore = new AuthThrottleStore($tmpThrottle);
$resetStore = new AuthResetTokenStore($tmpReset);
$kernel = new Kernel(new JwtService(), $store, null, null, null, null, null, null, null, null, null, $throttleStore, $resetStore);
$env = ['JWT_SECRET' => 'test-secret', 'DEBUG_PASSWORD_RESET_TOKEN' => 'true', 'NOW_TS' => 1710000000];

$forgot = $kernel->handle('POST', '/auth/forgot', 'req-forgot', [], ['email' => 'admin@local'], $env);
assertTrue(($forgot['status'] ?? 0) === 200, 'forgot password deve retornar 200');
$token = (string) ($forgot['body']['reset_token'] ?? '');
assertTrue($token !== '', 'forgot password com debug deve retornar token');

$reset = $kernel->handle('POST', '/auth/reset', 'req-reset', [], ['token' => $token, 'new_password' => 'admin4567'], $env);
assertTrue(($reset['status'] ?? 0) === 200, 'reset password deve retornar 200 com token válido');

$loginOld = $kernel->handle('POST', '/auth/login', 'req-old', [], ['email' => 'admin@local', 'password' => 'admin123'], $env);
assertTrue(($loginOld['status'] ?? 0) === 401, 'senha antiga nao deve autenticar apos reset');

$loginNew = $kernel->handle('POST', '/auth/login', 'req-new', [], ['email' => 'admin@local', 'password' => 'admin4567'], $env);
assertTrue(($loginNew['status'] ?? 0) === 200, 'senha nova deve autenticar apos reset');

$forgot2 = $kernel->handle('POST', '/auth/forgot', 'req-forgot-2', [], ['email' => 'admin@local'], $env);
$token2 = (string) ($forgot2['body']['reset_token'] ?? '');
$expiredEnv = ['JWT_SECRET' => 'test-secret', 'NOW_TS' => 1710005000];
$expired = $kernel->handle('POST', '/auth/reset', 'req-expired', [], ['token' => $token2, 'new_password' => 'admin9999'], $expiredEnv);
assertTrue(($expired['status'] ?? 0) === 422, 'token expirado deve ser rejeitado');

echo "OK: AuthPasswordResetHashTest" . PHP_EOL;

$throttleStore->reset();
$resetStore->reset();
