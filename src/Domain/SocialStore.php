<?php

declare(strict_types=1);

namespace App\Domain;

use PDO;

final class SocialStore
{
    private string $storagePath;
    private ?PDO $pdo;

    public function __construct(?string $storagePath = null, ?PDO $pdo = null)
    {
        $this->storagePath = $storagePath ?? __DIR__ . '/../../data/social_store.json';
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
        $driver = strtolower((string) (getenv('SOCIAL_STORE_DRIVER') ?: 'json'));
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
            return [
                'families' => [],
                'dependents' => [],
                'children' => [],
                'familySeq' => 1,
                'dependentSeq' => 1,
                'childSeq' => 1,
                'visits' => [],
                'visitSeq' => 1,
            ];
        }

        $raw = file_get_contents($this->storagePath);
        $decoded = json_decode($raw ?: '{}', true);
        if (!is_array($decoded)) {
            return [
                'families' => [],
                'dependents' => [],
                'children' => [],
                'familySeq' => 1,
                'dependentSeq' => 1,
                'childSeq' => 1,
                'visits' => [],
                'visitSeq' => 1,
            ];
        }

        $decoded['families'] = $decoded['families'] ?? [];
        $decoded['dependents'] = $decoded['dependents'] ?? [];
        $decoded['children'] = $decoded['children'] ?? [];
        $decoded['familySeq'] = (int) ($decoded['familySeq'] ?? 1);
        $decoded['dependentSeq'] = (int) ($decoded['dependentSeq'] ?? 1);
        $decoded['childSeq'] = (int) ($decoded['childSeq'] ?? 1);
        $decoded['visits'] = $decoded['visits'] ?? [];
        $decoded['visitSeq'] = (int) ($decoded['visitSeq'] ?? 1);

        return $decoded;
    }

    /** @param array<string,mixed> $data */
    private function save(array $data): void
    {
        file_put_contents($this->storagePath, json_encode($data, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT));
    }

    /** @return array<int,array<string,mixed>> */
    public function listFamilies(): array
    {
        if ($this->pdo !== null) {
            $stmt = $this->pdo->query('SELECT id, responsible_full_name, responsible_cpf FROM families ORDER BY id ASC');
            return $stmt->fetchAll() ?: [];
        }

        $data = $this->load();
        return array_values($data['families']);
    }

    /** @return array<string,mixed>|null */
    public function getFamily(int $id): ?array
    {
        if ($this->pdo !== null) {
            $stmt = $this->pdo->prepare('SELECT id, responsible_full_name, responsible_cpf FROM families WHERE id = :id LIMIT 1');
            $stmt->execute(['id' => $id]);
            $item = $stmt->fetch();
            return is_array($item) ? $item : null;
        }

        $data = $this->load();
        return $data['families'][(string) $id] ?? null;
    }

    /** @return array<string,mixed> */
    public function createFamily(string $name, string $cpf): array
    {
        if ($this->pdo !== null) {
            $stmt = $this->pdo->prepare('INSERT INTO families (responsible_full_name, responsible_cpf) VALUES (:name, :cpf)');
            $stmt->execute(['name' => $name, 'cpf' => $cpf]);
            $id = (int) $this->pdo->lastInsertId();
            return ['id' => $id, 'responsible_full_name' => $name, 'responsible_cpf' => $cpf];
        }

        $data = $this->load();
        $id = (int) $data['familySeq'];
        $data['familySeq'] = $id + 1;

        $family = ['id' => $id, 'responsible_full_name' => $name, 'responsible_cpf' => $cpf];
        $data['families'][(string) $id] = $family;
        $this->save($data);

        return $family;
    }

    /** @return array<string,mixed>|null */
    public function updateFamily(int $id, string $name, string $cpf): ?array
    {
        if ($this->pdo !== null) {
            $stmt = $this->pdo->prepare('UPDATE families SET responsible_full_name = :name, responsible_cpf = :cpf WHERE id = :id');
            $stmt->execute(['name' => $name, 'cpf' => $cpf, 'id' => $id]);
            if ($stmt->rowCount() === 0) {
                return null;
            }
            return $this->getFamily($id);
        }

        $data = $this->load();
        if (!isset($data['families'][(string) $id])) {
            return null;
        }

        $data['families'][(string) $id]['responsible_full_name'] = $name;
        $data['families'][(string) $id]['responsible_cpf'] = $cpf;
        $this->save($data);

        return $data['families'][(string) $id];
    }

    public function deleteFamily(int $id): bool
    {
        if ($this->pdo !== null) {
            $stmt = $this->pdo->prepare('DELETE FROM families WHERE id = :id');
            $stmt->execute(['id' => $id]);
            return $stmt->rowCount() > 0;
        }

        $data = $this->load();
        if (!isset($data['families'][(string) $id])) {
            return false;
        }

        unset($data['families'][(string) $id]);

        foreach ($data['dependents'] as $depId => $dependent) {
            if ((int) ($dependent['family_id'] ?? 0) === $id) {
                unset($data['dependents'][$depId]);
            }
        }

        foreach ($data['children'] as $childId => $child) {
            if ((int) ($child['family_id'] ?? 0) === $id) {
                unset($data['children'][$childId]);
            }
        }

        $this->save($data);
        return true;
    }

    public function familyCpfExists(string $cpf, ?int $ignoreId = null): bool
    {
        if ($this->pdo !== null) {
            if ($ignoreId !== null) {
                $stmt = $this->pdo->prepare('SELECT 1 FROM families WHERE responsible_cpf = :cpf AND id <> :id LIMIT 1');
                $stmt->execute(['cpf' => $cpf, 'id' => $ignoreId]);
            } else {
                $stmt = $this->pdo->prepare('SELECT 1 FROM families WHERE responsible_cpf = :cpf LIMIT 1');
                $stmt->execute(['cpf' => $cpf]);
            }
            return (bool) $stmt->fetchColumn();
        }

        $data = $this->load();
        foreach ($data['families'] as $family) {
            if ((string) $family['responsible_cpf'] === $cpf && (int) $family['id'] !== (int) ($ignoreId ?? 0)) {
                return true;
            }
        }

        return false;
    }

    /** @return array<int,array<string,mixed>> */
    public function listDependents(): array
    {
        if ($this->pdo !== null) {
            $stmt = $this->pdo->query('SELECT id, family_id, full_name FROM dependents ORDER BY id ASC');
            return $stmt->fetchAll() ?: [];
        }

        $data = $this->load();
        return array_values($data['dependents']);
    }

    /** @return array<string,mixed>|null */
    public function createDependent(int $familyId, string $name): ?array
    {
        if ($this->pdo !== null) {
            if ($this->getFamily($familyId) === null) {
                return null;
            }
            $stmt = $this->pdo->prepare('INSERT INTO dependents (family_id, full_name) VALUES (:family_id, :full_name)');
            $stmt->execute(['family_id' => $familyId, 'full_name' => $name]);
            return ['id' => (int) $this->pdo->lastInsertId(), 'family_id' => $familyId, 'full_name' => $name];
        }

        $data = $this->load();
        if (!isset($data['families'][(string) $familyId])) {
            return null;
        }

        $id = (int) $data['dependentSeq'];
        $data['dependentSeq'] = $id + 1;

        $dependent = ['id' => $id, 'family_id' => $familyId, 'full_name' => $name];
        $data['dependents'][(string) $id] = $dependent;
        $this->save($data);

        return $dependent;
    }

    public function deleteDependent(int $id): bool
    {
        if ($this->pdo !== null) {
            $stmt = $this->pdo->prepare('DELETE FROM dependents WHERE id = :id');
            $stmt->execute(['id' => $id]);
            return $stmt->rowCount() > 0;
        }

        $data = $this->load();
        if (!isset($data['dependents'][(string) $id])) {
            return false;
        }

        unset($data['dependents'][(string) $id]);
        $this->save($data);

        return true;
    }

    /** @return array<int,array<string,mixed>> */
    public function listChildren(): array
    {
        if ($this->pdo !== null) {
            $stmt = $this->pdo->query('SELECT id, family_id, full_name FROM children ORDER BY id ASC');
            return $stmt->fetchAll() ?: [];
        }

        $data = $this->load();
        return array_values($data['children']);
    }

    /** @return array<string,mixed>|null */
    public function createChild(int $familyId, string $name): ?array
    {
        if ($this->pdo !== null) {
            if ($this->getFamily($familyId) === null) {
                return null;
            }
            $stmt = $this->pdo->prepare('INSERT INTO children (family_id, full_name) VALUES (:family_id, :full_name)');
            $stmt->execute(['family_id' => $familyId, 'full_name' => $name]);
            return ['id' => (int) $this->pdo->lastInsertId(), 'family_id' => $familyId, 'full_name' => $name];
        }

        $data = $this->load();
        if (!isset($data['families'][(string) $familyId])) {
            return null;
        }

        $id = (int) $data['childSeq'];
        $data['childSeq'] = $id + 1;

        $child = ['id' => $id, 'family_id' => $familyId, 'full_name' => $name];
        $data['children'][(string) $id] = $child;
        $this->save($data);

        return $child;
    }

    public function deleteChild(int $id): bool
    {
        if ($this->pdo !== null) {
            $stmt = $this->pdo->prepare('DELETE FROM children WHERE id = :id');
            $stmt->execute(['id' => $id]);
            return $stmt->rowCount() > 0;
        }

        $data = $this->load();
        if (!isset($data['children'][(string) $id])) {
            return false;
        }

        unset($data['children'][(string) $id]);
        $this->save($data);

        return true;
    }



    /** @return array<int,array<string,mixed>> */
    public function listVisits(?string $status = null): array
    {
        if ($this->pdo !== null) {
            if ($status !== null && $status !== '') {
                $stmt = $this->pdo->prepare('SELECT id, person_id, family_id, scheduled_for, status, notes, completed_at FROM visits WHERE status = :status ORDER BY scheduled_for ASC, id ASC');
                $stmt->execute(['status' => $status]);
                return $stmt->fetchAll() ?: [];
            }
            $stmt = $this->pdo->query('SELECT id, person_id, family_id, scheduled_for, status, notes, completed_at FROM visits ORDER BY scheduled_for ASC, id ASC');
            return $stmt->fetchAll() ?: [];
        }

        $data = $this->load();
        $items = array_values($data['visits']);
        if ($status === null || $status === '') {
            return $items;
        }

        return array_values(array_filter($items, static fn(array $item): bool => (string) ($item['status'] ?? '') === $status));
    }

    /** @return array<string,mixed>|null */
    public function createVisit(int $personId, ?int $familyId, string $scheduledFor, string $notes = ''): ?array
    {
        if ($this->pdo !== null) {
            $stmt = $this->pdo->prepare('INSERT INTO visits (person_id, family_id, scheduled_for, status, notes, created_at, updated_at) VALUES (:person_id, :family_id, :scheduled_for, :status, :notes, NOW(), NOW())');
            $stmt->execute([
                'person_id' => $personId,
                'family_id' => $familyId,
                'scheduled_for' => $scheduledFor,
                'status' => 'pendente',
                'notes' => $notes !== '' ? $notes : null,
            ]);
            return [
                'id' => (int) $this->pdo->lastInsertId(),
                'person_id' => $personId,
                'family_id' => $familyId,
                'scheduled_for' => $scheduledFor,
                'status' => 'pendente',
                'notes' => $notes,
                'completed_at' => null,
            ];
        }

        $data = $this->load();
        $id = (int) $data['visitSeq'];
        $data['visitSeq'] = $id + 1;

        $visit = [
            'id' => $id,
            'person_id' => $personId,
            'family_id' => $familyId,
            'scheduled_for' => $scheduledFor,
            'status' => 'pendente',
            'notes' => $notes,
            'completed_at' => null,
        ];
        $data['visits'][(string) $id] = $visit;
        $this->save($data);

        return $visit;
    }

    /** @return array<string,mixed>|null */
    public function completeVisit(int $id, string $completedAt): ?array
    {
        if ($this->pdo !== null) {
            $stmt = $this->pdo->prepare('UPDATE visits SET status = :status, completed_at = :completed_at, updated_at = NOW() WHERE id = :id');
            $stmt->execute(['status' => 'concluida', 'completed_at' => $completedAt, 'id' => $id]);
            if ($stmt->rowCount() === 0) {
                return null;
            }
            $find = $this->pdo->prepare('SELECT id, person_id, family_id, scheduled_for, status, notes, completed_at FROM visits WHERE id = :id LIMIT 1');
            $find->execute(['id' => $id]);
            $item = $find->fetch();
            return is_array($item) ? $item : null;
        }

        $data = $this->load();
        if (!isset($data['visits'][(string) $id])) {
            return null;
        }
        $data['visits'][(string) $id]['status'] = 'concluida';
        $data['visits'][(string) $id]['completed_at'] = $completedAt;
        $this->save($data);

        return $data['visits'][(string) $id];
    }
    public function reset(): void
    {
        if ($this->pdo !== null) {
            $this->pdo->exec('DELETE FROM children');
            $this->pdo->exec('DELETE FROM dependents');
            $this->pdo->exec('DELETE FROM families');
            return;
        }

        if (file_exists($this->storagePath)) {
            unlink($this->storagePath);
        }
    }
}
