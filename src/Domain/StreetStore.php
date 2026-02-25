<?php

declare(strict_types=1);

namespace App\Domain;

final class StreetStore
{
    private string $storagePath;

    public function __construct(?string $storagePath = null)
    {
        $this->storagePath = $storagePath ?? __DIR__ . '/../../data/street_store.json';
        $dir = dirname($this->storagePath);
        if (!is_dir($dir)) {
            mkdir($dir, 0777, true);
        }
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
        return array_values($this->load()['people']);
    }

    /** @return array<string,mixed>|null */
    public function getPerson(int $id): ?array
    {
        return $this->load()['people'][(string) $id] ?? null;
    }

    /** @return array<string,mixed> */
    public function createPerson(string $name, bool $concluded, bool $consentAccepted, string $signatureName): array
    {
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
        if (file_exists($this->storagePath)) {
            unlink($this->storagePath);
        }
    }
}
