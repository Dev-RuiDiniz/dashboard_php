<?php

declare(strict_types=1);

namespace App\Http;

use App\Audit\AuditLogger;
use App\Auth\JwtService;
use App\Auth\UserStore;

final class Kernel
{
    public function __construct(
        private ?JwtService $jwtService = null,
        private ?UserStore $userStore = null,
        private ?AuditLogger $auditLogger = null,
    ) {
        $this->jwtService = $this->jwtService ?? new JwtService();
        $this->userStore = $this->userStore ?? new UserStore();
    }

    /**
     * @param array<string, string> $headers
     * @param array<string, mixed> $payload
     * @param array<string, mixed> $env
     * @return array{status:int, body:array<string,mixed>}
     */
    public function handle(
        string $method,
        string $path,
        string $requestId,
        array $headers = [],
        array $payload = [],
        array $env = [],
    ): array {
        if ($method === 'GET' && $path === '/health') {
            return [
                'status' => 200,
                'body' => [
                    'status' => 'ok',
                    'service' => 'dashboard_php',
                    'request_id' => $requestId,
                ],
            ];
        }

        if ($method === 'GET' && $path === '/ready') {
            $isReady = ($env['APP_READY'] ?? getenv('APP_READY') ?: 'true') !== 'false';

            return [
                'status' => $isReady ? 200 : 503,
                'body' => [
                    'status' => $isReady ? 'ready' : 'not_ready',
                    'service' => 'dashboard_php',
                    'request_id' => $requestId,
                ],
            ];
        }

        if ($method === 'POST' && $path === '/auth/login') {
            $email = (string) ($payload['email'] ?? '');
            $password = (string) ($payload['password'] ?? '');
            $user = $this->userStore->authenticate($email, $password);

            if (!$user) {
                $this->audit('auth.login_failed', $requestId, ['email' => $email]);
                return [
                    'status' => 401,
                    'body' => ['error' => 'invalid_credentials', 'request_id' => $requestId],
                ];
            }

            $secret = (string) ($env['JWT_SECRET'] ?? getenv('JWT_SECRET') ?: 'dev-secret');
            $token = $this->jwtService->issueToken((string) $user['email'], $secret);
            $this->audit('auth.login_success', $requestId, ['user_email' => (string) $user['email']]);

            return [
                'status' => 200,
                'body' => [
                    'access_token' => $token,
                    'token_type' => 'bearer',
                    'request_id' => $requestId,
                ],
            ];
        }

        if ($method === 'GET' && $path === '/me') {
            $authHeader = $headers['Authorization'] ?? $headers['authorization'] ?? '';
            $token = str_starts_with($authHeader, 'Bearer ') ? substr($authHeader, 7) : '';
            if ($token === '') {
                return ['status' => 401, 'body' => ['error' => 'missing_token', 'request_id' => $requestId]];
            }

            $secret = (string) ($env['JWT_SECRET'] ?? getenv('JWT_SECRET') ?: 'dev-secret');
            $claims = $this->jwtService->verifyToken($token, $secret);
            if (!$claims || !isset($claims['sub'])) {
                return ['status' => 401, 'body' => ['error' => 'invalid_token', 'request_id' => $requestId]];
            }

            $user = $this->userStore->findByEmail((string) $claims['sub']);
            if (!$user) {
                return ['status' => 401, 'body' => ['error' => 'unknown_user', 'request_id' => $requestId]];
            }

            return [
                'status' => 200,
                'body' => [
                    'id' => $user['id'],
                    'name' => $user['name'],
                    'email' => $user['email'],
                    'role' => $user['role'],
                    'permissions' => $user['permissions'],
                    'request_id' => $requestId,
                ],
            ];
        }

        if ($method === 'POST' && $path === '/auth/logout') {
            $this->audit('auth.logout', $requestId, []);
            return [
                'status' => 200,
                'body' => [
                    'status' => 'logged_out',
                    'request_id' => $requestId,
                ],
            ];
        }

        if ($method === 'GET' && $path === '/admin/ping') {
            $authHeader = $headers['Authorization'] ?? $headers['authorization'] ?? '';
            $token = str_starts_with($authHeader, 'Bearer ') ? substr($authHeader, 7) : '';
            $secret = (string) ($env['JWT_SECRET'] ?? getenv('JWT_SECRET') ?: 'dev-secret');
            $claims = $this->jwtService->verifyToken($token, $secret);
            $user = $claims && isset($claims['sub']) ? $this->userStore->findByEmail((string) $claims['sub']) : null;

            if (!$user || (($user['role'] ?? '') !== 'Admin')) {
                $this->audit('auth.forbidden', $requestId, ['path' => '/admin/ping']);
                return ['status' => 403, 'body' => ['error' => 'forbidden', 'request_id' => $requestId]];
            }

            return ['status' => 200, 'body' => ['status' => 'ok', 'scope' => 'admin', 'request_id' => $requestId]];
        }

        if (!in_array($method, ['GET', 'POST'], true)) {
            return ['status' => 405, 'body' => ['error' => 'method_not_allowed', 'request_id' => $requestId]];
        }

        return ['status' => 404, 'body' => ['error' => 'not_found', 'request_id' => $requestId]];
    }

    /** @param array<string, scalar|null> $context */
    private function audit(string $action, string $requestId, array $context): void
    {
        if (!$this->auditLogger) {
            return;
        }

        $this->auditLogger->record($action, array_merge(['request_id' => $requestId], $context));
    }
}
