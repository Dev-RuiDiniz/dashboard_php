<?php

declare(strict_types=1);

require_once __DIR__ . '/../src/Http/Kernel.php';
require_once __DIR__ . '/../src/Http/RequestContext.php';
require_once __DIR__ . '/../src/Observability/JsonLogger.php';

use App\Http\Kernel;
use App\Http\RequestContext;
use App\Observability\JsonLogger;

$start = microtime(true);

$method = $_SERVER['REQUEST_METHOD'] ?? 'GET';
$path = parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH) ?: '/';
$headers = function_exists('getallheaders') ? getallheaders() : [];

$requestContext = new RequestContext();
$requestId = $requestContext->resolveRequestId($headers);

$kernel = new Kernel();
$response = $kernel->handle($method, $path, $requestId);

http_response_code($response['status']);
header('Content-Type: application/json; charset=utf-8');
header('X-Request-Id: ' . $requestId);

echo json_encode($response['body'], JSON_UNESCAPED_UNICODE);

$durationMs = (int) round((microtime(true) - $start) * 1000);
$logger = new JsonLogger();
$logger->info('http_request', [
    'request_id' => $requestId,
    'method' => $method,
    'path' => $path,
    'status' => $response['status'],
    'duration_ms' => $durationMs,
]);
