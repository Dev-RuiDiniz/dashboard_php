<?php

declare(strict_types=1);

namespace App\Domain;

final class AuthThrottleStore
{
    private string $storagePath;

    public function __construct(?string $storagePath = null)
    {
        $this->storagePath = $storagePath ?? __DIR__ . '/../../data/auth_throttle.json';
        $dir = dirname($this->storagePath);
        if (!is_dir($dir)) {
            mkdir($dir, 0777, true);
        }
    }

    /** @return array<string,mixed> */
    private function load(): array
    {
        if (!file_exists($this->storagePath)) {
            return ['attempts' => []];
        }
        $d = json_decode(file_get_contents($this->storagePath) ?: '{}', true);
        return is_array($d) ? $d : ['attempts' => []];
    }

    /** @param array<string,mixed> $d */
    private function save(array $d): void
    {
        file_put_contents($this->storagePath, json_encode($d, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT));
    }

    public function registerFailure(string $identity, int $windowSeconds = 900, int $maxAttempts = 5): array
    {
        $now = time();
        $d = $this->load();
        $attempts = $d['attempts'][$identity] ?? [];
        $attempts = array_values(array_filter($attempts, static fn($ts) => is_int($ts) && ($now - $ts) <= $windowSeconds));
        $attempts[] = $now;
        $d['attempts'][$identity] = $attempts;
        $this->save($d);

        return [
            'blocked' => count($attempts) >= $maxAttempts,
            'attempts' => count($attempts),
        ];
    }

    public function clear(string $identity): void
    {
        $d = $this->load();
        unset($d['attempts'][$identity]);
        $this->save($d);
    }

    public function isBlocked(string $identity, int $windowSeconds = 900, int $maxAttempts = 5): bool
    {
        $now = time();
        $d = $this->load();
        $attempts = $d['attempts'][$identity] ?? [];
        $attempts = array_values(array_filter($attempts, static fn($ts) => is_int($ts) && ($now - $ts) <= $windowSeconds));
        return count($attempts) >= $maxAttempts;
    }

    public function reset(): void
    {
        if (file_exists($this->storagePath)) {
            unlink($this->storagePath);
        }
    }
}
