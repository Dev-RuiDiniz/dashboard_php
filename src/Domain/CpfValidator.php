<?php

declare(strict_types=1);

namespace App\Domain;

final class CpfValidator
{
    public function normalize(string $cpf): string
    {
        return preg_replace('/\D+/', '', $cpf) ?? '';
    }

    public function isValid(string $cpf): bool
    {
        $digits = $this->normalize($cpf);
        if (strlen($digits) !== 11 || preg_match('/^(\d)\1{10}$/', $digits) === 1) {
            return false;
        }

        for ($t = 9; $t < 11; $t++) {
            $sum = 0;
            for ($i = 0; $i < $t; $i++) {
                $sum += ((int) $digits[$i]) * (($t + 1) - $i);
            }

            $digit = ((10 * $sum) % 11) % 10;
            if ($digit !== (int) $digits[$t]) {
                return false;
            }
        }

        return true;
    }
}
