<?php

declare(strict_types=1);

namespace App\Domain;

use PDO;

final class StreetStore
{
    private string $storagePath;
    private ?PDO $pdo;

    public function __construct(?string $storagePath = null, ?PDO $pdo = null)
    {
        $this->storagePath = $storagePath ?? __DIR__ . '/../../data/street_store.json';
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
        $driver = strtolower((string) (getenv('STREET_STORE_DRIVER') ?: 'json'));
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
            return ['people' => [], 'referrals' => [], 'personSeq' => 1, 'referralSeq' => 1];
        }

        $raw = file_get_contents($this->storagePath);
        $decoded = json_decode($raw ?: '{}', true);
        if (!is_array($decoded)) {
            return ['people' => [], 'referrals' => [], 'personSeq' => 1, 'referralSeq' => 1];
        }

        $decoded['people'] = $decoded['people'] ?? [];
        $decoded['referrals'] = $decoded['referrals'] ?? [];
        $decoded['personSeq'] = (int) ($decoded['personSeq'] ?? 1);
        $decoded['referralSeq'] = (int) ($decoded['referralSeq'] ?? 1);

        return $decoded;
    }

    /** @param array<string,mixed> $data */
    private function save(array $data): void
    {
        file_put_contents($this->storagePath, json_encode($data, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT));
    }

    /** @return array<int,array<string,mixed>> */
    public function listPeople(): array
    {
        if ($this->pdo !== null) {
            $stmt = $this->pdo->query('SELECT id, full_name, concluded, consent_accepted, signature_name FROM street_residents ORDER BY id ASC');
            return $stmt->fetchAll() ?: [];
        }

        return array_values($this->load()['people']);
    }

    /** @return array<string,mixed>|null */
    public function getPerson(int $id): ?array
    {
        if ($this->pdo !== null) {
            $stmt = $this->pdo->prepare('SELECT id, full_name, concluded, consent_accepted, signature_name FROM street_residents WHERE id = :id LIMIT 1');
            $stmt->execute(['id' => $id]);
            $item = $stmt->fetch();
            return is_array($item) ? $item : null;
        }

        return $this->load()['people'][(string) $id] ?? null;
    }

    /** @return array<string,mixed> */
    public function createPerson(string $name, bool $concluded, bool $consentAccepted, string $signatureName): array
    {
        if ($this->pdo !== null) {
            $stmt = $this->pdo->prepare('INSERT INTO street_residents (full_name, concluded, consent_accepted, signature_name) VALUES (:full_name, :concluded, :consent_accepted, :signature_name)');
            $stmt->execute([
                'full_name' => $name,
                'concluded' => $concluded ? 1 : 0,
                'consent_accepted' => $consentAccepted ? 1 : 0,
                'signature_name' => $signatureName === '' ? null : $signatureName,
            ]);
            return [
                'id' => (int) $this->pdo->lastInsertId(),
                'full_name' => $name,
                'concluded' => $concluded,
                'consent_accepted' => $consentAccepted,
                'signature_name' => $signatureName,
            ];
        }

        $data = $this->load();
        $id = (int) $data['personSeq'];
        $data['personSeq'] = $id + 1;

        $person = [
            'id' => $id,
            'full_name' => $name,
            'concluded' => $concluded,
            'consent_accepted' => $consentAccepted,
            'signature_name' => $signatureName,
        ];

        $data['people'][(string) $id] = $person;
        $this->save($data);

        return $person;
    }

    /** @return array<string,mixed>|null */
    public function createReferral(int $personId, string $target): ?array
    {
        if ($this->pdo !== null) {
            if ($this->getPerson($personId) === null) {
                return null;
            }
            $stmt = $this->pdo->prepare('INSERT INTO street_referrals (street_resident_id, target, status) VALUES (:street_resident_id, :target, :status)');
            $stmt->execute([
                'street_resident_id' => $personId,
                'target' => $target,
                'status' => 'pendente',
            ]);

            return [
                'id' => (int) $this->pdo->lastInsertId(),
                'person_id' => $personId,
                'target' => $target,
                'status' => 'pendente',
            ];
        }

        $data = $this->load();
        if (!isset($data['people'][(string) $personId])) {
            return null;
        }

        $id = (int) $data['referralSeq'];
        $data['referralSeq'] = $id + 1;

        $referral = [
            'id' => $id,
            'person_id' => $personId,
            'target' => $target,
            'status' => 'pendente',
        ];

        $data['referrals'][(string) $id] = $referral;
        $this->save($data);

        return $referral;
    }

    /** @return array<string,mixed>|null */
    public function updateReferralStatus(int $id, string $status): ?array
    {
        if ($this->pdo !== null) {
            $stmt = $this->pdo->prepare('UPDATE street_referrals SET status = :status WHERE id = :id');
            $stmt->execute(['status' => $status, 'id' => $id]);
            if ($stmt->rowCount() === 0) {
                return null;
            }

            $query = $this->pdo->prepare('SELECT id, street_resident_id, target, status FROM street_referrals WHERE id = :id LIMIT 1');
            $query->execute(['id' => $id]);
            $item = $query->fetch();
            if (!is_array($item)) {
                return null;
            }

            return [
                'id' => (int) $item['id'],
                'person_id' => (int) $item['street_resident_id'],
                'target' => (string) $item['target'],
                'status' => (string) $item['status'],
            ];
        }

        $data = $this->load();
        if (!isset($data['referrals'][(string) $id])) {
            return null;
        }

        $data['referrals'][(string) $id]['status'] = $status;
        $this->save($data);

        return $data['referrals'][(string) $id];
    }

    public function reset(): void
    {
        if ($this->pdo !== null) {
            $this->pdo->exec('DELETE FROM street_referrals');
            $this->pdo->exec('DELETE FROM street_residents');
            return;
        }

        if (file_exists($this->storagePath)) {
            unlink($this->storagePath);
        }
    }
}
