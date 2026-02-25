<?php

declare(strict_types=1);

namespace App\Domain;

final class SocialStore
{
    private string $storagePath;

    public function __construct(?string $storagePath = null)
    {
        $this->storagePath = $storagePath ?? __DIR__ . '/../../data/social_store.json';
        $dir = dirname($this->storagePath);
        if (!is_dir($dir)) {
            mkdir($dir, 0777, true);
        }
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
            ];
        }

        $decoded['families'] = $decoded['families'] ?? [];
        $decoded['dependents'] = $decoded['dependents'] ?? [];
        $decoded['children'] = $decoded['children'] ?? [];
        $decoded['familySeq'] = (int) ($decoded['familySeq'] ?? 1);
        $decoded['dependentSeq'] = (int) ($decoded['dependentSeq'] ?? 1);
        $decoded['childSeq'] = (int) ($decoded['childSeq'] ?? 1);

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
        $data = $this->load();
        return array_values($data['families']);
    }

    /** @return array<string,mixed>|null */
    public function getFamily(int $id): ?array
    {
        $data = $this->load();
        return $data['families'][(string) $id] ?? null;
    }

    /** @return array<string,mixed> */
    public function createFamily(string $name, string $cpf): array
    {
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
        $data = $this->load();
        return array_values($data['dependents']);
    }

    /** @return array<string,mixed>|null */
    public function createDependent(int $familyId, string $name): ?array
    {
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
        $data = $this->load();
        return array_values($data['children']);
    }

    /** @return array<string,mixed>|null */
    public function createChild(int $familyId, string $name): ?array
    {
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
        $data = $this->load();
        if (!isset($data['children'][(string) $id])) {
            return false;
        }

        unset($data['children'][(string) $id]);
        $this->save($data);

        return true;
    }

    public function reset(): void
    {
        if (file_exists($this->storagePath)) {
            unlink($this->storagePath);
        }
    }
}
