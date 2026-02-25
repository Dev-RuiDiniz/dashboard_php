<?php

declare(strict_types=1);

$dsn = getenv('MYSQL_DSN') ?: '';
if ($dsn === '') {
    $host = getenv('MYSQL_HOST') ?: '127.0.0.1';
    $port = getenv('MYSQL_PORT') ?: '3306';
    $database = getenv('MYSQL_DATABASE') ?: 'dashboard_php';
    $charset = getenv('MYSQL_CHARSET') ?: 'utf8mb4';
    $dsn = sprintf('mysql:host=%s;port=%s;dbname=%s;charset=%s', $host, $port, $database, $charset);
}

$user = getenv('MYSQL_USER') ?: 'root';
$password = getenv('MYSQL_PASSWORD') ?: '';
$pdo = new PDO($dsn, $user, $password, [
    PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
]);

function loadJsonStore(string $file): array
{
    if (!file_exists($file)) {
        return [];
    }

    $raw = file_get_contents($file);
    $decoded = json_decode($raw ?: '{}', true);
    return is_array($decoded) ? $decoded : [];
}

$root = dirname(__DIR__);
$social = loadJsonStore($root . '/data/social_store.json');
$street = loadJsonStore($root . '/data/street_store.json');

if (isset($social['families']) && is_array($social['families'])) {
    $stmt = $pdo->prepare('INSERT INTO families (id, responsible_full_name, responsible_cpf) VALUES (:id, :name, :cpf) ON DUPLICATE KEY UPDATE responsible_full_name = VALUES(responsible_full_name), responsible_cpf = VALUES(responsible_cpf)');
    foreach ($social['families'] as $item) {
        $stmt->execute([
            'id' => (int) ($item['id'] ?? 0),
            'name' => (string) ($item['responsible_full_name'] ?? ''),
            'cpf' => (string) ($item['responsible_cpf'] ?? ''),
        ]);
    }
}

if (isset($social['dependents']) && is_array($social['dependents'])) {
    $stmt = $pdo->prepare('INSERT INTO dependents (id, family_id, full_name) VALUES (:id, :family_id, :full_name) ON DUPLICATE KEY UPDATE family_id = VALUES(family_id), full_name = VALUES(full_name)');
    foreach ($social['dependents'] as $item) {
        $stmt->execute([
            'id' => (int) ($item['id'] ?? 0),
            'family_id' => (int) ($item['family_id'] ?? 0),
            'full_name' => (string) ($item['full_name'] ?? ''),
        ]);
    }
}

if (isset($social['children']) && is_array($social['children'])) {
    $stmt = $pdo->prepare('INSERT INTO children (id, family_id, full_name) VALUES (:id, :family_id, :full_name) ON DUPLICATE KEY UPDATE family_id = VALUES(family_id), full_name = VALUES(full_name)');
    foreach ($social['children'] as $item) {
        $stmt->execute([
            'id' => (int) ($item['id'] ?? 0),
            'family_id' => (int) ($item['family_id'] ?? 0),
            'full_name' => (string) ($item['full_name'] ?? ''),
        ]);
    }
}

if (isset($street['people']) && is_array($street['people'])) {
    $stmt = $pdo->prepare('INSERT INTO street_residents (id, full_name, concluded, consent_accepted, signature_name) VALUES (:id, :full_name, :concluded, :consent_accepted, :signature_name) ON DUPLICATE KEY UPDATE full_name = VALUES(full_name), concluded = VALUES(concluded), consent_accepted = VALUES(consent_accepted), signature_name = VALUES(signature_name)');
    foreach ($street['people'] as $item) {
        $stmt->execute([
            'id' => (int) ($item['id'] ?? 0),
            'full_name' => (string) ($item['full_name'] ?? ''),
            'concluded' => !empty($item['concluded']) ? 1 : 0,
            'consent_accepted' => !empty($item['consent_accepted']) ? 1 : 0,
            'signature_name' => (string) ($item['signature_name'] ?? ''),
        ]);
    }
}

if (isset($street['referrals']) && is_array($street['referrals'])) {
    $stmt = $pdo->prepare('INSERT INTO street_referrals (id, street_resident_id, target, status) VALUES (:id, :street_resident_id, :target, :status) ON DUPLICATE KEY UPDATE street_resident_id = VALUES(street_resident_id), target = VALUES(target), status = VALUES(status)');
    foreach ($street['referrals'] as $item) {
        $stmt->execute([
            'id' => (int) ($item['id'] ?? 0),
            'street_resident_id' => (int) ($item['person_id'] ?? 0),
            'target' => (string) ($item['target'] ?? ''),
            'status' => (string) ($item['status'] ?? 'pendente'),
        ]);
    }
}

echo "OK: migrate_json_to_mysql" . PHP_EOL;
