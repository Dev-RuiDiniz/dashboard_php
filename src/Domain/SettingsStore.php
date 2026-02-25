<?php

declare(strict_types=1);

namespace App\Domain;

final class SettingsStore
{
    private string $storagePath;

    public function __construct(?string $storagePath = null)
    {
        $this->storagePath = $storagePath ?? __DIR__ . '/../../data/settings_store.json';
        $dir = dirname($this->storagePath);
        if (!is_dir($dir)) {
            mkdir($dir, 0777, true);
        }
    }

    /** @return array<string,mixed> */
    public function get(): array
    {
        if (!file_exists($this->storagePath)) {
            return [
                'max_deliveries_per_month' => 1,
                'min_months_since_last_delivery' => 1,
                'min_vulnerability_score' => 1,
                'require_documentation' => false,
            ];
        }

        $data = json_decode(file_get_contents($this->storagePath) ?: '{}', true);
        if (!is_array($data)) {
            return [
                'max_deliveries_per_month' => 1,
                'min_months_since_last_delivery' => 1,
                'min_vulnerability_score' => 1,
                'require_documentation' => false,
            ];
        }

        return $data;
    }

    /** @param array<string,mixed> $values */
    public function update(array $values): array
    {
        $current = $this->get();
        $merged = array_merge($current, $values);
        file_put_contents($this->storagePath, json_encode($merged, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT));
        return $merged;
    }

    public function reset(): void
    {
        if (file_exists($this->storagePath)) {
            unlink($this->storagePath);
        }
    }
}
