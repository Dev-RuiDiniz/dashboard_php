<?php

declare(strict_types=1);

namespace App\Http;

final class Kernel
{
    /**
     * @return array{status:int, body:array<string,mixed>}
     */
    public function handle(string $method, string $path, string $requestId, array $env = []): array
    {
        if ($method !== 'GET') {
            return [
                'status' => 405,
                'body' => [
                    'error' => 'method_not_allowed',
                    'request_id' => $requestId,
                ],
            ];
        }

        if ($path === '/health') {
            return [
                'status' => 200,
                'body' => [
                    'status' => 'ok',
                    'service' => 'dashboard_php',
                    'request_id' => $requestId,
                ],
            ];
        }

        if ($path === '/ready') {
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

        return [
            'status' => 404,
            'body' => [
                'error' => 'not_found',
                'request_id' => $requestId,
            ],
        ];
    }
}
