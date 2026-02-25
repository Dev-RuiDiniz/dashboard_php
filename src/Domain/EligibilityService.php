<?php

declare(strict_types=1);

namespace App\Domain;

final class EligibilityService
{
    /** @param array<string,mixed> $rules @param array<string,mixed> $input */
    public function evaluate(array $rules, array $input): array
    {
        $reasons = [];

        $deliveriesThisMonth = (int) ($input['deliveries_this_month'] ?? 0);
        $monthsSinceLastDelivery = (int) ($input['months_since_last_delivery'] ?? 0);
        $vulnerabilityScore = (int) ($input['vulnerability_score'] ?? 0);
        $hasDocumentation = (bool) ($input['has_documentation'] ?? false);

        if ($deliveriesThisMonth >= (int) ($rules['max_deliveries_per_month'] ?? 1)) {
            $reasons[] = 'max_deliveries_per_month_reached';
        }
        if ($monthsSinceLastDelivery < (int) ($rules['min_months_since_last_delivery'] ?? 1)) {
            $reasons[] = 'min_months_since_last_delivery_not_met';
        }
        if ($vulnerabilityScore < (int) ($rules['min_vulnerability_score'] ?? 1)) {
            $reasons[] = 'min_vulnerability_score_not_met';
        }
        if ((bool) ($rules['require_documentation'] ?? false) && !$hasDocumentation) {
            $reasons[] = 'documentation_required';
        }

        return [
            'eligible' => count($reasons) === 0,
            'reasons' => $reasons,
        ];
    }
}
