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
        // Bootstrap técnico: conteúdo tabular simples para evolução posterior a XLSX completo.
        $lines = ["id\tresponsible_full_name\tresponsible_cpf"];
        foreach ($families as $f) {
            $lines[] = sprintf(
                "%s\t%s\t%s",
                (string) ($f['id'] ?? ''),
                (string) ($f['responsible_full_name'] ?? ''),
                (string) ($f['responsible_cpf'] ?? ''),
            );
        }

        return implode("\n", $lines) . "\n";
    }

    /** @param array<int,array<string,mixed>> $families */
    public function buildPdf(array $families): string
    {
        // Bootstrap técnico: PDF textual simplificado para evoluir na Sprint de fidelidade visual.
        $content = "RELATORIO DE FAMILIAS\n\n";
        foreach ($families as $f) {
            $content .= sprintf(
                "- #%s %s (%s)\n",
                (string) ($f['id'] ?? ''),
                (string) ($f['responsible_full_name'] ?? ''),
                (string) ($f['responsible_cpf'] ?? ''),
            );
        }

        return $content;
    }
}
