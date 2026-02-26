<?php

declare(strict_types=1);

namespace App\Domain;

use DateTimeImmutable;
use PDO;

final class AuthResetTokenStore
{
    private string $storagePath;
    private ?PDO $pdo;

    public function __construct(?string $storagePath = null, ?PDO $pdo = null)
    {
        $this->storagePath = $storagePath ?? __DIR__ . '/../../data/auth_reset_tokens.json';
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
        $driver = strtolower((string) (getenv('AUTH_RESET_TOKEN_STORE_DRIVER') ?: 'json'));
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

        $username = getenv('MYSQL_USER') ?: 'root';
        $password = getenv('MYSQL_PASSWORD') ?: '';

        return new PDO($dsn, $username, $password, [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
        ]);
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
        $createdAtTs = $createdAt ?? time();

        if ($this->pdo !== null) {
            $stmt = $this->pdo->prepare(
                'INSERT INTO auth_reset_tokens (token_hash, email, expires_at, created_at, consumed_at) VALUES (:token_hash, :email, :expires_at, :created_at, NULL)'
            );
            $stmt->execute([
                'token_hash' => $tokenHash,
                'email' => $email,
                'expires_at' => $this->toSqlDateTime($expiresAt),
                'created_at' => $this->toSqlDateTime($createdAtTs),
            ]);

            return $token;
        }

        $d = $this->load();
        $d['tokens'][$tokenHash] = [
            'email' => $email,
            'expires_at' => $expiresAt,
            'created_at' => $createdAtTs,
        ];
        $this->save($d);

        return $token;
    }

    public function consumeToken(string $token, int $nowTs): ?string
    {
        $tokenHash = hash('sha256', $token);

        if ($this->pdo !== null) {
            $stmt = $this->pdo->prepare(
                'SELECT id, email, expires_at, consumed_at FROM auth_reset_tokens WHERE token_hash = :token_hash LIMIT 1'
            );
            $stmt->execute(['token_hash' => $tokenHash]);
            $row = $stmt->fetch();
            if (!is_array($row)) {
                return null;
            }

            if ($row['consumed_at'] !== null) {
                return null;
            }

            $expiresAt = strtotime((string) $row['expires_at']) ?: 0;
            $markConsumed = $this->pdo->prepare('UPDATE auth_reset_tokens SET consumed_at = :consumed_at WHERE id = :id AND consumed_at IS NULL');
            $markConsumed->execute(['consumed_at' => $this->toSqlDateTime($nowTs), 'id' => (int) $row['id']]);
            if ($markConsumed->rowCount() === 0) {
                return null;
            }

            if ($expiresAt < $nowTs) {
                return null;
            }

            return (string) ($row['email'] ?? '');
        }

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
        if ($this->pdo !== null) {
            $stmt = $this->pdo->prepare('DELETE FROM auth_reset_tokens WHERE expires_at < :now OR consumed_at IS NOT NULL');
            $stmt->execute(['now' => $this->toSqlDateTime($nowTs)]);
            return;
        }

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
        if ($this->pdo !== null) {
            $this->pdo->exec('DELETE FROM auth_reset_tokens');
            return;
        }

        if (file_exists($this->storagePath)) {
            unlink($this->storagePath);
        }
    }

    private function toSqlDateTime(int $timestamp): string
    {
        return (new DateTimeImmutable('@' . $timestamp))->setTimezone(new \DateTimeZone('UTC'))->format('Y-m-d H:i:s');
    }
}
