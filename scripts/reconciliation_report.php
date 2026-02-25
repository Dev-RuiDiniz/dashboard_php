<?php

declare(strict_types=1);

$argv = $_SERVER['argv'] ?? [];
$dataDir = __DIR__ . '/../data';

for ($i = 1; $i < count($argv); $i++) {
    if ($argv[$i] === '--data-dir' && isset($argv[$i + 1])) {
        $dataDir = (string) $argv[$i + 1];
        $i++;
    }
}

/** @return array<string,mixed> */
function loadStore(string $path): array
{
    if (!file_exists($path)) {
        return [];
    }

    $raw = file_get_contents($path);
    $decoded = json_decode($raw ?: '{}', true);
    return is_array($decoded) ? $decoded : [];
}

$social = loadStore($dataDir . '/social_store.json');
$street = loadStore($dataDir . '/street_store.json');
$delivery = loadStore($dataDir . '/delivery_store.json');
$equipment = loadStore($dataDir . '/equipment_store.json');
$settings = loadStore($dataDir . '/settings_store.json');

/** @param array<int|string,mixed> $items */
function countItems(array $items): int
{
    return count($items);
}

/** @param array<int|string,mixed> $items */
function sampleIds(array $items, string $idKey): array
{
    $out = [];
    foreach ($items as $item) {
        if (!is_array($item)) {
            continue;
        }
        if (!array_key_exists($idKey, $item)) {
            continue;
        }
        $out[] = (int) $item[$idKey];
        if (count($out) >= 5) {
            break;
        }
    }
    return $out;
}

$report = [
    'generated_at' => gmdate('c'),
    'data_dir' => realpath($dataDir) ?: $dataDir,
    'domains' => [
        'social' => [
            'families_total' => countItems($social['families'] ?? []),
            'dependents_total' => countItems($social['dependents'] ?? []),
            'children_total' => countItems($social['children'] ?? []),
            'sample_family_ids' => sampleIds($social['families'] ?? [], 'id'),
        ],
        'street' => [
            'people_total' => countItems($street['people'] ?? []),
            'referrals_total' => countItems($street['referrals'] ?? []),
            'sample_person_ids' => sampleIds($street['people'] ?? [], 'id'),
        ],
        'delivery' => [
            'events_total' => countItems($delivery['events'] ?? []),
            'invites_total' => countItems($delivery['invites'] ?? []),
            'withdrawals_total' => countItems($delivery['withdrawals'] ?? []),
            'sample_event_ids' => sampleIds($delivery['events'] ?? [], 'id'),
        ],
        'equipment' => [
            'equipments_total' => countItems($equipment['equipments'] ?? []),
            'loans_total' => countItems($equipment['loans'] ?? []),
            'sample_equipment_ids' => sampleIds($equipment['equipments'] ?? [], 'id'),
        ],
        'settings' => [
            'has_settings' => count($settings) > 0,
            'keys' => array_values(array_keys($settings)),
        ],
    ],
];

echo json_encode($report, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT) . PHP_EOL;
