<?php

declare(strict_types=1);

namespace App\Domain;

use PDO;

final class EquipmentStore
{
    private string $storagePath;
    private ?PDO $pdo;

    public function __construct(?string $storagePath = null, ?PDO $pdo = null)
    {
        $this->storagePath = $storagePath ?? __DIR__ . '/../../data/equipment_store.json';
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
        $driver = strtolower((string) (getenv('EQUIPMENT_STORE_DRIVER') ?: 'json'));
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
    private function load(): array
    {
        if (!file_exists($this->storagePath)) {
            return ['equipments' => [], 'loans' => [], 'equipmentSeq' => 1, 'loanSeq' => 1];
        }
        $d = json_decode(file_get_contents($this->storagePath) ?: '{}', true);
        if (!is_array($d)) {
            return ['equipments' => [], 'loans' => [], 'equipmentSeq' => 1, 'loanSeq' => 1];
        }
        $d['equipments'] = $d['equipments'] ?? [];
        $d['loans'] = $d['loans'] ?? [];
        $d['equipmentSeq'] = (int) ($d['equipmentSeq'] ?? 1);
        $d['loanSeq'] = (int) ($d['loanSeq'] ?? 1);
        return $d;
    }

    /** @param array<string,mixed> $d */
    private function save(array $d): void
    {
        file_put_contents($this->storagePath, json_encode($d, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT));
    }

    /** @return array<int,array<string,mixed>> */
    public function listEquipments(): array
    {
        if ($this->pdo !== null) {
            $stmt = $this->pdo->query('SELECT id, code, type, status, `condition`, notes FROM equipments ORDER BY id ASC');
            return $stmt->fetchAll() ?: [];
        }

        return array_values($this->load()['equipments']);
    }

    /** @return array<string,mixed> */
    public function createEquipment(string $type, string $condition, string $notes): array
    {
        if ($this->pdo !== null) {
            $codeQuery = $this->pdo->query('SELECT COALESCE(MAX(id),0)+1 AS next_id FROM equipments');
            $nextId = (int) (($codeQuery->fetch()['next_id'] ?? 1));
            $code = 'EQ-' . str_pad((string) $nextId, 4, '0', STR_PAD_LEFT);
            $stmt = $this->pdo->prepare('INSERT INTO equipments (code, type, status, `condition`, notes) VALUES (:code, :type, :status, :condition, :notes)');
            $stmt->execute(['code' => $code, 'type' => $type, 'status' => 'disponivel', 'condition' => $condition, 'notes' => $notes]);
            return ['id' => (int) $this->pdo->lastInsertId(), 'code' => $code, 'type' => $type, 'status' => 'disponivel', 'condition' => $condition, 'notes' => $notes];
        }

        $d = $this->load();
        $id = (int) $d['equipmentSeq'];
        $d['equipmentSeq'] = $id + 1;
        $code = 'EQ-' . str_pad((string) $id, 4, '0', STR_PAD_LEFT);
        $e = ['id' => $id, 'code' => $code, 'type' => $type, 'status' => 'disponivel', 'condition' => $condition, 'notes' => $notes];
        $d['equipments'][(string) $id] = $e;
        $this->save($d);
        return $e;
    }

    /** @return array<string,mixed>|null */
    public function updateEquipment(int $id, string $status, string $condition, string $notes): ?array
    {
        if (!in_array($status, ['disponivel', 'emprestado', 'manutencao'], true)) {
            return ['error' => 'invalid_status'];
        }

        if ($this->pdo !== null) {
            $stmt = $this->pdo->prepare('UPDATE equipments SET status = :status, `condition` = :condition, notes = :notes WHERE id = :id');
            $stmt->execute(['status' => $status, 'condition' => $condition, 'notes' => $notes, 'id' => $id]);
            if ($stmt->rowCount() === 0) {
                return null;
            }
            $get = $this->pdo->prepare('SELECT id, code, type, status, `condition`, notes FROM equipments WHERE id = :id LIMIT 1');
            $get->execute(['id' => $id]);
            $item = $get->fetch();
            return is_array($item) ? $item : null;
        }

        $d = $this->load();
        if (!isset($d['equipments'][(string) $id])) {
            return null;
        }
        $d['equipments'][(string) $id]['status'] = $status;
        $d['equipments'][(string) $id]['condition'] = $condition;
        $d['equipments'][(string) $id]['notes'] = $notes;
        $this->save($d);
        return $d['equipments'][(string) $id];
    }

    /** @return array<string,mixed>|null */
    public function createLoan(int $equipmentId, int $familyId, string $dueDate): ?array
    {
        if ($this->pdo !== null) {
            $eqStmt = $this->pdo->prepare('SELECT id, status FROM equipments WHERE id = :id LIMIT 1');
            $eqStmt->execute(['id' => $equipmentId]);
            $equipment = $eqStmt->fetch();
            if (!is_array($equipment)) {
                return null;
            }
            if ((string) $equipment['status'] !== 'disponivel') {
                return ['error' => 'equipment_unavailable'];
            }

            $stmt = $this->pdo->prepare('INSERT INTO equipment_loans (equipment_id, family_id, due_date, status) VALUES (:equipment_id, :family_id, :due_date, :status)');
            $stmt->execute(['equipment_id' => $equipmentId, 'family_id' => $familyId, 'due_date' => $dueDate, 'status' => 'aberto']);
            $this->pdo->prepare('UPDATE equipments SET status = :status WHERE id = :id')->execute(['status' => 'emprestado', 'id' => $equipmentId]);
            return ['id' => (int) $this->pdo->lastInsertId(), 'equipment_id' => $equipmentId, 'family_id' => $familyId, 'due_date' => $dueDate, 'status' => 'aberto'];
        }

        $d = $this->load();
        if (!isset($d['equipments'][(string) $equipmentId])) {
            return null;
        }
        if ((string) $d['equipments'][(string) $equipmentId]['status'] !== 'disponivel') {
            return ['error' => 'equipment_unavailable'];
        }
        $id = (int) $d['loanSeq'];
        $d['loanSeq'] = $id + 1;
        $loan = ['id' => $id, 'equipment_id' => $equipmentId, 'family_id' => $familyId, 'due_date' => $dueDate, 'status' => 'aberto'];
        $d['loans'][(string) $id] = $loan;
        $d['equipments'][(string) $equipmentId]['status'] = 'emprestado';
        $this->save($d);
        return $loan;
    }

    /** @return array<string,mixed>|null */
    public function returnLoan(int $loanId, string $condition, string $notes): ?array
    {
        if ($this->pdo !== null) {
            $loanStmt = $this->pdo->prepare('SELECT id, equipment_id, status FROM equipment_loans WHERE id = :id LIMIT 1');
            $loanStmt->execute(['id' => $loanId]);
            $loan = $loanStmt->fetch();
            if (!is_array($loan)) {
                return null;
            }
            if ((string) $loan['status'] !== 'aberto') {
                return ['error' => 'loan_closed'];
            }

            $this->pdo->prepare('UPDATE equipment_loans SET status = :status, return_condition = :return_condition, return_notes = :return_notes WHERE id = :id')->execute([
                'status' => 'devolvido',
                'return_condition' => $condition,
                'return_notes' => $notes,
                'id' => $loanId,
            ]);
            $this->pdo->prepare('UPDATE equipments SET status = :status, `condition` = :condition, notes = :notes WHERE id = :id')->execute([
                'status' => 'disponivel',
                'condition' => $condition,
                'notes' => $notes,
                'id' => (int) $loan['equipment_id'],
            ]);
            $out = $this->pdo->prepare('SELECT id, equipment_id, family_id, due_date, status, return_condition, return_notes FROM equipment_loans WHERE id = :id LIMIT 1');
            $out->execute(['id' => $loanId]);
            $item = $out->fetch();
            return is_array($item) ? $item : null;
        }

        $d = $this->load();
        if (!isset($d['loans'][(string) $loanId])) {
            return null;
        }
        if ((string) $d['loans'][(string) $loanId]['status'] !== 'aberto') {
            return ['error' => 'loan_closed'];
        }
        $equipId = (int) $d['loans'][(string) $loanId]['equipment_id'];
        $d['loans'][(string) $loanId]['status'] = 'devolvido';
        $d['loans'][(string) $loanId]['return_condition'] = $condition;
        $d['loans'][(string) $loanId]['return_notes'] = $notes;
        if (isset($d['equipments'][(string) $equipId])) {
            $d['equipments'][(string) $equipId]['status'] = 'disponivel';
            $d['equipments'][(string) $equipId]['condition'] = $condition;
            $d['equipments'][(string) $equipId]['notes'] = $notes;
        }
        $this->save($d);
        return $d['loans'][(string) $loanId];
    }

    /** @return array<int,array<string,mixed>> */
    public function listLoans(): array
    {
        if ($this->pdo !== null) {
            $stmt = $this->pdo->query('SELECT id, equipment_id, family_id, due_date, status, return_condition, return_notes FROM equipment_loans ORDER BY id ASC');
            return $stmt->fetchAll() ?: [];
        }

        return array_values($this->load()['loans']);
    }

    public function reset(): void
    {
        if ($this->pdo !== null) {
            $this->pdo->exec('DELETE FROM equipment_loans');
            $this->pdo->exec('DELETE FROM equipments');
            return;
        }

        if (file_exists($this->storagePath)) {
            unlink($this->storagePath);
        }
    }
}
