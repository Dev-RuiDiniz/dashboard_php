<?php

declare(strict_types=1);

namespace App\Domain;

final class AuthResetTokenStore
{
    private string $storagePath;

    public function __construct(?string $storagePath = null)
    {
        $this->storagePath = $storagePath ?? __DIR__ . '/../../data/auth_reset_tokens.json';
        $dir = dirname($this->storagePath);
        if (!is_dir($dir)) {
            mkdir($dir, 0777, true);
        }
    }

    /** @return array<string,mixed> */
    private function load(): array
    {
        if (!file_exists($this->storagePath)) {
            return ['tokens' => []];
        }
        $d = json_decode(file_get_contents($this->storagePath) ?: '{}', true);
        return is_array($d) ? $d : ['tokens' => []];
    }

    /** @param array<string,mixed> $d */
    private function save(array $d): void
    {
        file_put_contents($this->storagePath, json_encode($d, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT));
    }

    public function issueToken(string $email, int $expiresAt, ?int $createdAt = null): string
    {
        $token = bin2hex(random_bytes(24));
        $tokenHash = hash('sha256', $token);
        $d = $this->load();
        $d['tokens'][$tokenHash] = [
            'email' => $email,
            'expires_at' => $expiresAt,
            'created_at' => $createdAt ?? time(),
        ];
        $this->save($d);

        return $token;
    }

    public function consumeToken(string $token, int $nowTs): ?string
    {
        $tokenHash = hash('sha256', $token);
        $d = $this->load();
        $state = $d['tokens'][$tokenHash] ?? null;
        if (!is_array($state)) {
            return null;
        }

        unset($d['tokens'][$tokenHash]);
        $this->save($d);

        $expiresAt = (int) ($state['expires_at'] ?? 0);
        if ($expiresAt < $nowTs) {
            return null;
        }

        return (string) ($state['email'] ?? '');
    }

    public function purgeExpired(int $nowTs): void
    {
        $d = $this->load();
        $tokens = $d['tokens'] ?? [];
        if (!is_array($tokens)) {
            $this->save(['tokens' => []]);
            return;
        }

        foreach ($tokens as $tokenHash => $row) {
            if (!is_array($row) || (int) ($row['expires_at'] ?? 0) < $nowTs) {
                unset($tokens[$tokenHash]);
            }
        }

        $this->save(['tokens' => $tokens]);
    }

    public function reset(): void
    {
        if (file_exists($this->storagePath)) {
            unlink($this->storagePath);
        }
    }
}
