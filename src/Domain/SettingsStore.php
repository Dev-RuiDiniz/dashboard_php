<?php

declare(strict_types=1);

namespace App\Domain;

use PDO;

final class SettingsStore
{
    private string $storagePath;
    private ?PDO $pdo;

    public function __construct(?string $storagePath = null, ?PDO $pdo = null)
    {
        $this->storagePath = $storagePath ?? __DIR__ . '/../../data/settings_store.json';
        $this->pdo = $pdo ?? $this->resolvePdoFromEnvironment();

        if ($this->pdo === null) {
            $dir = dirname($this->storagePath);
            if (!is_dir($dir)) {
                mkdir($dir, 0777, true);
            }
        }
    }

    private function resolvePdoFromEnvironment(): ?PDO
    {
        $driver = strtolower((string) (getenv('SETTINGS_STORE_DRIVER') ?: 'json'));
        if ($driver !== 'mysql') {
            return null;
        }

        $dsn = getenv('MYSQL_DSN') ?: '';
        if ($dsn === '') {
            $host = getenv('MYSQL_HOST') ?: '127.0.0.1';
            $port = getenv('MYSQL_PORT') ?: '3306';
            $database = getenv('MYSQL_DATABASE') ?: 'dashboard_php';
            $charset = getenv('MYSQL_CHARSET') ?: 'utf8mb4';
            $dsn = sprintf('mysql:host=%s;port=%s;dbname=%s;charset=%s', $host, $port, $database, $charset);
        }

        return new PDO($dsn, getenv('MYSQL_USER') ?: 'root', getenv('MYSQL_PASSWORD') ?: '', [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
        ]);
    }

    /** @return array<string,mixed> */
    private function defaults(): array
    {
        return [
            'max_deliveries_per_month' => 1,
            'min_months_since_last_delivery' => 1,
            'min_vulnerability_score' => 1,
            'require_documentation' => false,
        ];
    }

    /** @return array<string,mixed> */
    public function get(): array
    {
        if ($this->pdo !== null) {
            $stmt = $this->pdo->query('SELECT max_deliveries_per_month, min_months_since_last_delivery, min_vulnerability_score, require_documentation FROM eligibility_settings ORDER BY id DESC LIMIT 1');
            $row = $stmt->fetch();
            if (!is_array($row)) {
                return $this->defaults();
            }
            return [
                'max_deliveries_per_month' => (int) $row['max_deliveries_per_month'],
                'min_months_since_last_delivery' => (int) $row['min_months_since_last_delivery'],
                'min_vulnerability_score' => (int) $row['min_vulnerability_score'],
                'require_documentation' => (bool) $row['require_documentation'],
            ];
        }

        if (!file_exists($this->storagePath)) {
            return $this->defaults();
        }

        $data = json_decode(file_get_contents($this->storagePath) ?: '{}', true);
        if (!is_array($data)) {
            return $this->defaults();
        }

        return $data;
    }

    /** @param array<string,mixed> $values
     *  @return array<string,mixed>
     */
    public function update(array $values): array
    {
        $current = $this->get();
        $merged = array_merge($current, $values);

        if ($this->pdo !== null) {
            $stmt = $this->pdo->prepare('INSERT INTO eligibility_settings (max_deliveries_per_month, min_months_since_last_delivery, min_vulnerability_score, require_documentation) VALUES (:max_deliveries_per_month, :min_months_since_last_delivery, :min_vulnerability_score, :require_documentation)');
            $stmt->execute([
                'max_deliveries_per_month' => (int) ($merged['max_deliveries_per_month'] ?? 1),
                'min_months_since_last_delivery' => (int) ($merged['min_months_since_last_delivery'] ?? 1),
                'min_vulnerability_score' => (int) ($merged['min_vulnerability_score'] ?? 1),
                'require_documentation' => !empty($merged['require_documentation']) ? 1 : 0,
            ]);
            return $this->get();
        }

        file_put_contents($this->storagePath, json_encode($merged, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT));
        return $merged;
    }

    public function reset(): void
    {
        if ($this->pdo !== null) {
            $this->pdo->exec('DELETE FROM eligibility_settings');
            return;
        }

        if (file_exists($this->storagePath)) {
            unlink($this->storagePath);
        }
    }
}
