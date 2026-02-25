<?php

declare(strict_types=1);

namespace App\Auth;

final class JwtService
{
    public function issueToken(string $subject, string $secret, int $ttlSeconds = 3600): string
    {
        $header = ['alg' => 'HS256', 'typ' => 'JWT'];
        $payload = [
            'sub' => $subject,
            'iat' => time(),
            'exp' => time() + $ttlSeconds,
        ];

        $segments = [
            $this->base64UrlEncode(json_encode($header, JSON_UNESCAPED_UNICODE)),
            $this->base64UrlEncode(json_encode($payload, JSON_UNESCAPED_UNICODE)),
        ];

        $signature = hash_hmac('sha256', implode('.', $segments), $secret, true);
        $segments[] = $this->base64UrlEncode($signature);

        return implode('.', $segments);
    }

    /**
     * @return array<string, mixed>|null
     */
    public function verifyToken(string $token, string $secret): ?array
    {
        $parts = explode('.', $token);
        if (count($parts) !== 3) {
            return null;
        }

        [$header64, $payload64, $signature64] = $parts;
        $expected = $this->base64UrlEncode(hash_hmac('sha256', $header64 . '.' . $payload64, $secret, true));

        if (!hash_equals($expected, $signature64)) {
            return null;
        }

        $payload = json_decode($this->base64UrlDecode($payload64), true);
        if (!is_array($payload) || !isset($payload['exp']) || time() >= (int) $payload['exp']) {
            return null;
        }

        return $payload;
    }

    private function base64UrlEncode(string $input): string
    {
        return rtrim(strtr(base64_encode($input), '+/', '-_'), '=');
    }

    private function base64UrlDecode(string $input): string
    {
        $remainder = strlen($input) % 4;
        if ($remainder > 0) {
            $input .= str_repeat('=', 4 - $remainder);
        }

        return base64_decode(strtr($input, '-_', '+/')) ?: '';
    }
}
