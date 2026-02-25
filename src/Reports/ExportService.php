<?php

declare(strict_types=1);

namespace App\Reports;

final class ExportService
{
    /** @param array<int,array<string,mixed>> $families */
    public function buildCsv(array $families): string
    {
        $lines = ['id,responsible_full_name,responsible_cpf'];
        foreach ($families as $f) {
            $id = (string) ($f['id'] ?? '');
            $name = str_replace('"', '""', (string) ($f['responsible_full_name'] ?? ''));
            $cpf = (string) ($f['responsible_cpf'] ?? '');
            $lines[] = sprintf('%s,"%s",%s', $id, $name, $cpf);
        }

        return implode("\n", $lines) . "\n";
    }

    /** @param array<int,array<string,mixed>> $families */
    public function buildXlsx(array $families): string
    {
        $xml = [];
        $xml[] = '<?xml version="1.0" encoding="UTF-8"?>';
        $xml[] = '<Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet"';
        $xml[] = ' xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet">';
        $xml[] = '  <Worksheet ss:Name="families">';
        $xml[] = '    <Table>';
        $xml[] = $this->spreadsheetRow(['id', 'responsible_full_name', 'responsible_cpf']);

        foreach ($families as $f) {
            $xml[] = $this->spreadsheetRow([
                (string) ($f['id'] ?? ''),
                (string) ($f['responsible_full_name'] ?? ''),
                (string) ($f['responsible_cpf'] ?? ''),
            ]);
        }

        $xml[] = '    </Table>';
        $xml[] = '  </Worksheet>';
        $xml[] = '</Workbook>';

        return implode("\n", $xml) . "\n";
    }

    /** @param array<int,string> $cells */
    private function spreadsheetRow(array $cells): string
    {
        $row = '      <Row>';
        foreach ($cells as $cell) {
            $safe = htmlspecialchars($cell, ENT_XML1 | ENT_QUOTES, 'UTF-8');
            $row .= '<Cell><Data ss:Type="String">' . $safe . '</Data></Cell>';
        }
        $row .= '</Row>';
        return $row;
    }

    /** @param array<int,array<string,mixed>> $families */
    public function buildPdf(array $families): string
    {
        $textLines = ['RELATORIO DE FAMILIAS', ''];
        foreach ($families as $f) {
            $textLines[] = sprintf(
                '#%s %s (%s)',
                (string) ($f['id'] ?? ''),
                (string) ($f['responsible_full_name'] ?? ''),
                (string) ($f['responsible_cpf'] ?? ''),
            );
        }

        return $this->buildMinimalPdf($textLines);
    }

    /** @param array<int,string> $lines */
    private function buildMinimalPdf(array $lines): string
    {
        $escape = static fn(string $v): string => str_replace(['\\', '(', ')'], ['\\\\', '\\(', '\\)'], $v);

        $streamLines = ['BT', '/F1 12 Tf', '50 780 Td', '(RELATORIO DE FAMILIAS) Tj'];
        $offsetY = 760;
        foreach ($lines as $idx => $line) {
            if ($idx < 2) {
                continue;
            }
            $streamLines[] = sprintf('50 %d Td (%s) Tj', $offsetY, $escape($line));
            $offsetY -= 16;
        }
        $streamLines[] = 'ET';
        $stream = implode("\n", $streamLines) . "\n";

        $objects = [];
        $objects[] = "1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n";
        $objects[] = "2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n";
        $objects[] = "3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>\nendobj\n";
        $objects[] = "4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n";
        $objects[] = "5 0 obj\n<< /Length " . strlen($stream) . " >>\nstream\n" . $stream . "endstream\nendobj\n";

        $pdf = "%PDF-1.4\n";
        $offsets = [0];
        foreach ($objects as $obj) {
            $offsets[] = strlen($pdf);
            $pdf .= $obj;
        }

        $xrefPos = strlen($pdf);
        $pdf .= "xref\n0 6\n";
        $pdf .= "0000000000 65535 f \n";
        for ($i = 1; $i <= 5; $i++) {
            $pdf .= sprintf("%010d 00000 n \n", $offsets[$i]);
        }
        $pdf .= "trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n" . $xrefPos . "\n%%EOF\n";

        return $pdf;
    }
}
