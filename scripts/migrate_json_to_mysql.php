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

$delivery = loadJsonStore($root . '/data/delivery_store.json');
$equipment = loadJsonStore($root . '/data/equipment_store.json');
$settings = loadJsonStore($root . '/data/settings_store.json');

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


if (isset($delivery['events']) && is_array($delivery['events'])) {
    $stmt = $pdo->prepare('INSERT INTO delivery_events (id, name, event_date, status) VALUES (:id, :name, :event_date, :status) ON DUPLICATE KEY UPDATE name = VALUES(name), event_date = VALUES(event_date), status = VALUES(status)');
    foreach ($delivery['events'] as $item) {
        $stmt->execute([
            'id' => (int) ($item['id'] ?? 0),
            'name' => (string) ($item['name'] ?? ''),
            'event_date' => (string) ($item['event_date'] ?? '1970-01-01'),
            'status' => (string) ($item['status'] ?? 'aberto'),
        ]);
    }
}

if (isset($delivery['invites']) && is_array($delivery['invites'])) {
    $stmt = $pdo->prepare('INSERT INTO delivery_invites (id, delivery_event_id, family_id, withdrawal_code, status) VALUES (:id, :delivery_event_id, :family_id, :withdrawal_code, :status) ON DUPLICATE KEY UPDATE delivery_event_id = VALUES(delivery_event_id), family_id = VALUES(family_id), withdrawal_code = VALUES(withdrawal_code), status = VALUES(status)');
    foreach ($delivery['invites'] as $item) {
        $stmt->execute([
            'id' => (int) ($item['id'] ?? 0),
            'delivery_event_id' => (int) ($item['event_id'] ?? 0),
            'family_id' => (int) ($item['family_id'] ?? 0),
            'withdrawal_code' => (string) ($item['withdrawal_code'] ?? ''),
            'status' => (string) ($item['status'] ?? 'presente'),
        ]);
    }
}

if (isset($delivery['withdrawals']) && is_array($delivery['withdrawals'])) {
    $stmt = $pdo->prepare('INSERT INTO delivery_withdrawals (id, delivery_event_id, family_id, signature_accepted, signature_name, status) VALUES (:id, :delivery_event_id, :family_id, :signature_accepted, :signature_name, :status) ON DUPLICATE KEY UPDATE delivery_event_id = VALUES(delivery_event_id), family_id = VALUES(family_id), signature_accepted = VALUES(signature_accepted), signature_name = VALUES(signature_name), status = VALUES(status)');
    foreach ($delivery['withdrawals'] as $item) {
        $stmt->execute([
            'id' => (int) ($item['id'] ?? 0),
            'delivery_event_id' => (int) ($item['event_id'] ?? 0),
            'family_id' => (int) ($item['family_id'] ?? 0),
            'signature_accepted' => !empty($item['signature_accepted']) ? 1 : 0,
            'signature_name' => (string) ($item['signature_name'] ?? ''),
            'status' => (string) ($item['status'] ?? 'retirou'),
        ]);
    }
}

if (isset($equipment['equipments']) && is_array($equipment['equipments'])) {
    $stmt = $pdo->prepare('INSERT INTO equipments (id, code, type, status, `condition`, notes) VALUES (:id, :code, :type, :status, :condition, :notes) ON DUPLICATE KEY UPDATE code = VALUES(code), type = VALUES(type), status = VALUES(status), `condition` = VALUES(`condition`), notes = VALUES(notes)');
    foreach ($equipment['equipments'] as $item) {
        $stmt->execute([
            'id' => (int) ($item['id'] ?? 0),
            'code' => (string) ($item['code'] ?? ''),
            'type' => (string) ($item['type'] ?? ''),
            'status' => (string) ($item['status'] ?? 'disponivel'),
            'condition' => (string) ($item['condition'] ?? ''),
            'notes' => (string) ($item['notes'] ?? ''),
        ]);
    }
}

if (isset($equipment['loans']) && is_array($equipment['loans'])) {
    $stmt = $pdo->prepare('INSERT INTO equipment_loans (id, equipment_id, family_id, due_date, status, return_condition, return_notes) VALUES (:id, :equipment_id, :family_id, :due_date, :status, :return_condition, :return_notes) ON DUPLICATE KEY UPDATE equipment_id = VALUES(equipment_id), family_id = VALUES(family_id), due_date = VALUES(due_date), status = VALUES(status), return_condition = VALUES(return_condition), return_notes = VALUES(return_notes)');
    foreach ($equipment['loans'] as $item) {
        $stmt->execute([
            'id' => (int) ($item['id'] ?? 0),
            'equipment_id' => (int) ($item['equipment_id'] ?? 0),
            'family_id' => (int) ($item['family_id'] ?? 0),
            'due_date' => (string) ($item['due_date'] ?? '1970-01-01'),
            'status' => (string) ($item['status'] ?? 'aberto'),
            'return_condition' => (string) ($item['return_condition'] ?? ''),
            'return_notes' => (string) ($item['return_notes'] ?? ''),
        ]);
    }
}

if (is_array($settings) && count($settings) > 0) {
    $stmt = $pdo->prepare('INSERT INTO eligibility_settings (max_deliveries_per_month, min_months_since_last_delivery, min_vulnerability_score, require_documentation) VALUES (:max_deliveries_per_month, :min_months_since_last_delivery, :min_vulnerability_score, :require_documentation)');
    $stmt->execute([
        'max_deliveries_per_month' => (int) ($settings['max_deliveries_per_month'] ?? 1),
        'min_months_since_last_delivery' => (int) ($settings['min_months_since_last_delivery'] ?? 1),
        'min_vulnerability_score' => (int) ($settings['min_vulnerability_score'] ?? 1),
        'require_documentation' => !empty($settings['require_documentation']) ? 1 : 0,
    ]);
}

echo "OK: migrate_json_to_mysql" . PHP_EOL;
