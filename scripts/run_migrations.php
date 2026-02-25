<?php

declare(strict_types=1);

$migrationDir = __DIR__ . '/../database/migrations';
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

$files = glob($migrationDir . '/*.sql');
sort($files);

foreach ($files as $file) {
    $sql = file_get_contents($file);
    if (!is_string($sql) || trim($sql) === '') {
        continue;
    }

    $pdo->exec($sql);
    echo 'applied: ' . basename($file) . PHP_EOL;
}
