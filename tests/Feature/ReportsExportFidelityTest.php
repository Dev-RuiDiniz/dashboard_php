<?php

declare(strict_types=1);

require_once __DIR__ . '/../../src/Reports/ExportService.php';

use App\Reports\ExportService;

function assertTrue(bool $condition, string $message): void
{
    if (!$condition) {
        fwrite(STDERR, 'Assertion failed: ' . $message . PHP_EOL);
        exit(1);
    }
}

$service = new ExportService();
$families = [
    ['id' => 1, 'responsible_full_name' => 'Maria Silva', 'responsible_cpf' => '52998224725'],
];

$csv = $service->buildCsv($families);
$csvGolden = file_get_contents(__DIR__ . '/../../docs/sprints/artifacts/golden_exports/families.csv');
assertTrue(is_string($csvGolden) && $csv === $csvGolden, 'csv deve casar com golden file');

$xlsx = $service->buildXlsx($families);
$xlsxGoldenHeader = file_get_contents(__DIR__ . '/../../docs/sprints/artifacts/golden_exports/families.xlsx.xml');
assertTrue(is_string($xlsxGoldenHeader), 'golden de xlsx deve existir');
assertTrue(str_contains($xlsx, '<?xml version="1.0" encoding="UTF-8"?>'), 'xlsx deve conter declaração xml');
assertTrue(str_contains($xlsx, '<Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet"'), 'xlsx deve conter workbook spreadsheetml');
assertTrue(str_contains($xlsx, '<Worksheet ss:Name="families">'), 'xlsx deve ter worksheet families');

$pdf = $service->buildPdf($families);
$pdfSignature = file_get_contents(__DIR__ . '/../../docs/sprints/artifacts/golden_exports/families.pdf.signature.txt');
assertTrue(is_string($pdfSignature), 'assinatura de pdf deve existir');
assertTrue(str_starts_with($pdf, "%PDF-1.4\n"), 'pdf deve iniciar com assinatura PDF');
assertTrue(str_contains($pdf, 'RELATORIO DE FAMILIAS'), 'pdf deve conter título no conteúdo');

echo 'OK: ReportsExportFidelityTest' . PHP_EOL;
