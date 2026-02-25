<?php

declare(strict_types=1);

require_once __DIR__ . '/../../src/Http/Kernel.php';
require_once __DIR__ . '/../../src/Auth/JwtService.php';
require_once __DIR__ . '/../../src/Auth/UserStore.php';
require_once __DIR__ . '/../../src/Domain/CpfValidator.php';
require_once __DIR__ . '/../../src/Domain/SocialStore.php';
require_once __DIR__ . '/../../src/Domain/StreetStore.php';
require_once __DIR__ . '/../../src/Audit/AuditLogger.php';
require_once __DIR__ . '/../../src/Observability/JsonLogger.php';

use App\Audit\AuditLogger;
use App\Auth\JwtService;
use App\Auth\UserStore;
use App\Http\Kernel;
use App\Observability\JsonLogger;

final class MemoryJsonLogger extends JsonLogger
{
    /** @var array<int, array<string, scalar|null>> */
    public array $entries = [];

    public function info(string $message, array $context = []): void
    {
        $this->entries[] = array_merge(['message' => $message], $context);
    }
}

function assertTrue(bool $condition, string $message): void
{
    if (!$condition) {
        fwrite(STDERR, "Assertion failed: {$message}" . PHP_EOL);
        exit(1);
    }
}

$memoryLogger = new MemoryJsonLogger();
$auditLogger = new AuditLogger($memoryLogger);
$kernel = new Kernel(new JwtService(), new UserStore(), $auditLogger);
$env = ['JWT_SECRET' => 'test-secret'];

$loginFail = $kernel->handle('POST', '/auth/login', 'req-fail', [], ['email' => 'admin@local', 'password' => 'x'], $env);
assertTrue($loginFail['status'] === 401, 'login inválido deve retornar 401');

$loginOk = $kernel->handle('POST', '/auth/login', 'req-ok', [], ['email' => 'admin@local', 'password' => 'admin123'], $env);
assertTrue($loginOk['status'] === 200, 'login válido deve retornar 200');
assertTrue(isset($loginOk['body']['access_token']), 'login deve retornar access_token');
$token = (string) $loginOk['body']['access_token'];

$meMissing = $kernel->handle('GET', '/me', 'req-me-missing', [], [], $env);
assertTrue($meMissing['status'] === 401, '/me sem token deve retornar 401');

$meOk = $kernel->handle('GET', '/me', 'req-me-ok', ['Authorization' => 'Bearer ' . $token], [], $env);
assertTrue($meOk['status'] === 200, '/me com token válido deve retornar 200');
assertTrue(($meOk['body']['email'] ?? '') === 'admin@local', '/me deve retornar usuário autenticado');

$opLogin = $kernel->handle('POST', '/auth/login', 'req-op', [], ['email' => 'operador@local', 'password' => 'operador123'], $env);
$opToken = (string) ($opLogin['body']['access_token'] ?? '');
$forbidden = $kernel->handle('GET', '/admin/ping', 'req-forbidden', ['Authorization' => 'Bearer ' . $opToken], [], $env);
assertTrue($forbidden['status'] === 403, 'rota admin deve bloquear operador');

$logout = $kernel->handle('POST', '/auth/logout', 'req-logout', [], [], $env);
assertTrue($logout['status'] === 200, 'logout deve retornar 200');

$actions = array_values(array_filter(array_map(static fn($e) => $e['action'] ?? null, $memoryLogger->entries)));
assertTrue(in_array('auth.login_failed', $actions, true), 'auditoria deve registrar login_failed');
assertTrue(in_array('auth.login_success', $actions, true), 'auditoria deve registrar login_success');
assertTrue(in_array('auth.forbidden', $actions, true), 'auditoria deve registrar forbidden');
assertTrue(in_array('auth.logout', $actions, true), 'auditoria deve registrar logout');

echo "OK: AuthRbacAuditTest" . PHP_EOL;
