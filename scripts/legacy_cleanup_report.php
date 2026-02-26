<?php

declare(strict_types=1);

$root = realpath(__DIR__ . '/..') ?: dirname(__DIR__);

$policy = [
    'runtime_keep_patterns' => [
        'src/',
        'public/',
        'routes/',
        'database/migrations/',
        'docs/',
        'scripts/',
        'tests/',
        '.github/',
    ],
    'legacy_review_paths' => [
        'frontend/legacy',
        'igreja_dashboard_python',
    ],
    'retention_rule' => 'Artefatos fora do runtime principal devem ser inventariados e removidos/arquivados após validação de dependências.',
];

$inventory = [];
foreach ($policy['legacy_review_paths'] as $relativePath) {
    $fullPath = $root . '/' . $relativePath;
    if (!file_exists($fullPath)) {
        $inventory[] = [
            'path' => $relativePath,
            'exists' => false,
            'files_count' => 0,
            'total_bytes' => 0,
            'action' => 'none',
        ];
        continue;
    }

    $filesCount = 0;
    $totalBytes = 0;
    $iterator = new RecursiveIteratorIterator(
        new RecursiveDirectoryIterator($fullPath, FilesystemIterator::SKIP_DOTS)
    );
    foreach ($iterator as $fileInfo) {
        if ($fileInfo->isFile()) {
            $filesCount++;
            $totalBytes += (int) $fileInfo->getSize();
        }
    }

    $inventory[] = [
        'path' => $relativePath,
        'exists' => true,
        'files_count' => $filesCount,
        'total_bytes' => $totalBytes,
        'action' => 'archive_or_remove_after_validation',
    ];
}

$report = [
    'generated_at' => gmdate('c'),
    'policy' => $policy,
    'inventory' => $inventory,
    'next_action' => 'Submeter inventário para aprovação técnica e executar limpeza em janela controlada.',
];

echo json_encode($report, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT) . PHP_EOL;
