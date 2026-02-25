<?php

declare(strict_types=1);

namespace App\Observability;

class JsonLogger
{
    /**
     * @param array<string, scalar|null> $context
     */
    public function info(string $message, array $context = []): void
    {
        $payload = array_merge(
            [
                'timestamp' => gmdate('c'),
                'level' => 'INFO',
                'message' => $message,
            ],
            $context,
        );

        file_put_contents('php://stdout', json_encode($payload, JSON_UNESCAPED_UNICODE) . PHP_EOL);
    }
}
