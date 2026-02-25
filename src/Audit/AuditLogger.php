<?php

declare(strict_types=1);

namespace App\Audit;

use App\Observability\JsonLogger;

final class AuditLogger
{
    public function __construct(private JsonLogger $logger)
    {
    }

    /** @param array<string, scalar|null> $context */
    public function record(string $action, array $context = []): void
    {
        $this->logger->info('audit_event', array_merge(['action' => $action], $context));
    }
}
