<?php

declare(strict_types=1);

namespace App\Domain;

use PDO;

final class DeliveryStore
{
    private string $storagePath;
    private ?PDO $pdo;

    public function __construct(?string $storagePath = null, ?PDO $pdo = null)
    {
        $this->storagePath = $storagePath ?? __DIR__ . '/../../data/delivery_store.json';
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
        $driver = strtolower((string) (getenv('DELIVERY_STORE_DRIVER') ?: 'json'));
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
            return ['events' => [], 'invites' => [], 'withdrawals' => [], 'eventSeq' => 1, 'inviteSeq' => 1, 'withdrawSeq' => 1];
        }
        $d = json_decode(file_get_contents($this->storagePath) ?: '{}', true);
        if (!is_array($d)) {
            return ['events' => [], 'invites' => [], 'withdrawals' => [], 'eventSeq' => 1, 'inviteSeq' => 1, 'withdrawSeq' => 1];
        }
        $d['events'] = $d['events'] ?? [];
        $d['invites'] = $d['invites'] ?? [];
        $d['withdrawals'] = $d['withdrawals'] ?? [];
        $d['eventSeq'] = (int) ($d['eventSeq'] ?? 1);
        $d['inviteSeq'] = (int) ($d['inviteSeq'] ?? 1);
        $d['withdrawSeq'] = (int) ($d['withdrawSeq'] ?? 1);
        return $d;
    }

    /** @param array<string,mixed> $d */
    private function save(array $d): void
    {
        file_put_contents($this->storagePath, json_encode($d, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT));
    }

    /** @return array<int,array<string,mixed>> */
    public function listEvents(): array
    {
        if ($this->pdo !== null) {
            $stmt = $this->pdo->query('SELECT id, name, event_date, status, published_at FROM delivery_events ORDER BY id ASC');
            return $stmt->fetchAll() ?: [];
        }

        return array_values($this->load()['events']);
    }

    /** @return array<string,mixed> */
    public function createEvent(string $name, string $date): array
    {
        if ($this->pdo !== null) {
            $stmt = $this->pdo->prepare('INSERT INTO delivery_events (name, event_date, status) VALUES (:name, :event_date, :status)');
            $stmt->execute(['name' => $name, 'event_date' => $date, 'status' => 'aberto']);
            return ['id' => (int) $this->pdo->lastInsertId(), 'name' => $name, 'event_date' => $date, 'status' => 'aberto', 'published_at' => null];
        }

        $d = $this->load();
        $id = (int) $d['eventSeq'];
        $d['eventSeq'] = $id + 1;
        $event = ['id' => $id, 'name' => $name, 'event_date' => $date, 'status' => 'aberto', 'published_at' => null];
        $d['events'][(string) $id] = $event;
        $this->save($d);
        return $event;
    }

    /** @return array<string,mixed>|null */
    public function inviteFamily(int $eventId, int $familyId): ?array
    {
        if ($this->pdo !== null) {
            $exists = $this->pdo->prepare('SELECT id, delivery_event_id, family_id, ticket_number, withdrawal_code, status FROM delivery_invites WHERE delivery_event_id = :event_id AND family_id = :family_id LIMIT 1');
            $exists->execute(['event_id' => $eventId, 'family_id' => $familyId]);
            $row = $exists->fetch();
            if (is_array($row)) {
                return ['id' => (int) $row['id'], 'event_id' => (int) $row['delivery_event_id'], 'family_id' => (int) $row['family_id'], 'ticket_number' => (int) ($row['ticket_number'] ?? 0), 'withdrawal_code' => (string) $row['withdrawal_code'], 'status' => (string) $row['status']];
            }

            $event = $this->pdo->prepare('SELECT id, status FROM delivery_events WHERE id = :id LIMIT 1');
            $event->execute(['id' => $eventId]);
            $eventRow = $event->fetch();
            if (!is_array($eventRow)) {
                return null;
            }
            if ((string) ($eventRow['status'] ?? '') === 'publicado') {
                return ['error' => 'event_published_immutable'];
            }

            $nextTicketStmt = $this->pdo->prepare('SELECT COALESCE(MAX(ticket_number), 0) + 1 AS next_ticket FROM delivery_invites WHERE delivery_event_id = :event_id');
            $nextTicketStmt->execute(['event_id' => $eventId]);
            $nextTicketRow = $nextTicketStmt->fetch();
            $nextTicket = (int) ($nextTicketRow['next_ticket'] ?? 1);
            $code = strtoupper(substr(hash('sha256', $eventId . '-' . $familyId . '-' . $nextTicket . '-' . uniqid('', true)), 0, 6));
            $insert = $this->pdo->prepare('INSERT INTO delivery_invites (delivery_event_id, family_id, ticket_number, withdrawal_code, status) VALUES (:event_id, :family_id, :ticket_number, :code, :status)');
            $insert->execute(['event_id' => $eventId, 'family_id' => $familyId, 'ticket_number' => $nextTicket, 'code' => $code, 'status' => 'presente']);
            return ['id' => (int) $this->pdo->lastInsertId(), 'event_id' => $eventId, 'family_id' => $familyId, 'ticket_number' => $nextTicket, 'withdrawal_code' => $code, 'status' => 'presente'];
        }

        $d = $this->load();
        if (!isset($d['events'][(string) $eventId])) {
            return null;
        }
        if (((string) ($d['events'][(string) $eventId]['status'] ?? '')) === 'publicado') {
            return ['error' => 'event_published_immutable'];
        }
        foreach ($d['invites'] as $inv) {
            if ((int) $inv['event_id'] === $eventId && (int) $inv['family_id'] === $familyId) {
                return $inv;
            }
        }
        $id = (int) $d['inviteSeq'];
        $d['inviteSeq'] = $id + 1;
        $maxTicket = 0;
        foreach ($d['invites'] as $existingInvite) {
            if ((int) ($existingInvite['event_id'] ?? 0) === $eventId) {
                $maxTicket = max($maxTicket, (int) ($existingInvite['ticket_number'] ?? 0));
            }
        }
        $ticketNumber = $maxTicket + 1;
        $code = strtoupper(substr(hash('sha256', $eventId . '-' . $familyId . '-' . $ticketNumber), 0, 6));
        $invite = ['id' => $id, 'event_id' => $eventId, 'family_id' => $familyId, 'ticket_number' => $ticketNumber, 'withdrawal_code' => $code, 'status' => 'presente'];
        $d['invites'][(string) $id] = $invite;
        $this->save($d);
        return $invite;
    }

    /** @return array<string,mixed>|null */
    public function publishEvent(int $eventId, string $publishedAt): ?array
    {
        if ($this->pdo !== null) {
            $stmt = $this->pdo->prepare('UPDATE delivery_events SET status = :status, published_at = :published_at WHERE id = :id');
            $stmt->execute(['status' => 'publicado', 'published_at' => $publishedAt, 'id' => $eventId]);
            if ($stmt->rowCount() === 0) {
                $find = $this->pdo->prepare('SELECT id, name, event_date, status, published_at FROM delivery_events WHERE id = :id LIMIT 1');
                $find->execute(['id' => $eventId]);
                $item = $find->fetch();
                return is_array($item) ? $item : null;
            }
            $find = $this->pdo->prepare('SELECT id, name, event_date, status, published_at FROM delivery_events WHERE id = :id LIMIT 1');
            $find->execute(['id' => $eventId]);
            $item = $find->fetch();
            return is_array($item) ? $item : null;
        }

        $d = $this->load();
        if (!isset($d['events'][(string) $eventId])) {
            return null;
        }
        $d['events'][(string) $eventId]['status'] = 'publicado';
        $d['events'][(string) $eventId]['published_at'] = $publishedAt;
        $this->save($d);
        return $d['events'][(string) $eventId];
    }

    public function hasFamilyWithdrawalInMonth(int $familyId, string $eventDate): bool
    {
        $month = substr($eventDate, 0, 7);

        if ($this->pdo !== null) {
            $stmt = $this->pdo->prepare('SELECT 1 FROM delivery_withdrawals w INNER JOIN delivery_events e ON e.id = w.delivery_event_id WHERE w.family_id = :family_id AND DATE_FORMAT(e.event_date, "%Y-%m") = :month LIMIT 1');
            $stmt->execute(['family_id' => $familyId, 'month' => $month]);
            return (bool) $stmt->fetchColumn();
        }

        $d = $this->load();
        foreach ($d['withdrawals'] as $w) {
            if ((int) $w['family_id'] !== $familyId) {
                continue;
            }
            $eid = (string) $w['event_id'];
            $date = (string) ($d['events'][$eid]['event_date'] ?? '');
            if (substr($date, 0, 7) === $month) {
                return true;
            }
        }
        return false;
    }

    /** @return array<string,mixed>|null */
    public function registerWithdrawal(int $eventId, int $familyId, bool $signatureAccepted, string $signatureName): ?array
    {
        if ($this->pdo !== null) {
            $eventStmt = $this->pdo->prepare('SELECT id, event_date FROM delivery_events WHERE id = :id LIMIT 1');
            $eventStmt->execute(['id' => $eventId]);
            $event = $eventStmt->fetch();
            if (!is_array($event)) {
                return null;
            }
            if ($this->hasFamilyWithdrawalInMonth($familyId, (string) $event['event_date'])) {
                return ['error' => 'duplicate_month'];
            }
            if (!$signatureAccepted || trim($signatureName) === '') {
                return ['error' => 'signature_required'];
            }

            $stmt = $this->pdo->prepare('INSERT INTO delivery_withdrawals (delivery_event_id, family_id, signature_accepted, signature_name, status) VALUES (:event_id, :family_id, :signature_accepted, :signature_name, :status)');
            $stmt->execute([
                'event_id' => $eventId,
                'family_id' => $familyId,
                'signature_accepted' => 1,
                'signature_name' => $signatureName,
                'status' => 'retirou',
            ]);

            return ['id' => (int) $this->pdo->lastInsertId(), 'event_id' => $eventId, 'family_id' => $familyId, 'signature_accepted' => true, 'signature_name' => $signatureName, 'status' => 'retirou'];
        }

        $d = $this->load();
        if (!isset($d['events'][(string) $eventId])) {
            return null;
        }
        if ($this->hasFamilyWithdrawalInMonth($familyId, (string) $d['events'][(string) $eventId]['event_date'])) {
            return ['error' => 'duplicate_month'];
        }
        if (!$signatureAccepted || trim($signatureName) === '') {
            return ['error' => 'signature_required'];
        }
        $id = (int) $d['withdrawSeq'];
        $d['withdrawSeq'] = $id + 1;
        $w = ['id' => $id, 'event_id' => $eventId, 'family_id' => $familyId, 'signature_accepted' => $signatureAccepted, 'signature_name' => $signatureName, 'status' => 'retirou'];
        $d['withdrawals'][(string) $id] = $w;
        $this->save($d);
        return $w;
    }

    public function reset(): void
    {
        if ($this->pdo !== null) {
            $this->pdo->exec('DELETE FROM delivery_withdrawals');
            $this->pdo->exec('DELETE FROM delivery_invites');
            $this->pdo->exec('DELETE FROM delivery_events');
            return;
        }

        if (file_exists($this->storagePath)) {
            unlink($this->storagePath);
        }
    }
}
