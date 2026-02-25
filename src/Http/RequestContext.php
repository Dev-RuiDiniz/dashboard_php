<?php

declare(strict_types=1);

namespace App\Http;

final class RequestContext
{
    public function resolveRequestId(array $headers): string
    {
        $headerKey = 'X-Request-Id';
        $requestId = $headers[$headerKey] ?? $headers[strtolower($headerKey)] ?? null;

        if (is_string($requestId) && trim($requestId) !== '') {
            return trim($requestId);
        }

        return bin2hex(random_bytes(16));
    }
}
