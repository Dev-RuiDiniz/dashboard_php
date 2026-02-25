<?php

declare(strict_types=1);

require_once __DIR__ . '/../src/Http/Kernel.php';
require_once __DIR__ . '/../src/Http/RequestContext.php';
require_once __DIR__ . '/../src/Observability/JsonLogger.php';
require_once __DIR__ . '/../src/Auth/JwtService.php';
require_once __DIR__ . '/../src/Auth/UserStore.php';
require_once __DIR__ . '/../src/Domain/CpfValidator.php';
require_once __DIR__ . '/../src/Domain/SocialStore.php';
require_once __DIR__ . '/../src/Domain/StreetStore.php';
require_once __DIR__ . '/../src/Domain/DeliveryStore.php';
require_once __DIR__ . '/../src/Domain/EquipmentStore.php';
require_once __DIR__ . '/../src/Audit/AuditLogger.php';
require_once __DIR__ . '/../src/Reports/ExportService.php';

use App\Audit\AuditLogger;
use App\Http\Kernel;
use App\Http\RequestContext;
use App\Observability\JsonLogger;

$start = microtime(true);
$method = $_SERVER['REQUEST_METHOD'] ?? 'GET';
$path = parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH) ?: '/';
$headers = function_exists('getallheaders') ? getallheaders() : [];

$rawInput = file_get_contents('php://input');
$payload = json_decode($rawInput ?: '{}', true);
if (!is_array($payload)) {
    $payload = [];
}

$requestContext = new RequestContext();
$requestId = $requestContext->resolveRequestId($headers);

$logger = new JsonLogger();
$auditLogger = new AuditLogger($logger);
$kernel = new Kernel(auditLogger: $auditLogger);
$response = $kernel->handle($method, $path, $requestId, $headers, $payload);

http_response_code($response['status']);
header('X-Request-Id: ' . $requestId);

if (isset($response['body']['__raw'])) {
    $contentType = (string) ($response['body']['__content_type'] ?? 'application/octet-stream');
    header('Content-Type: ' . $contentType);
    if (isset($response['body']['__file_name'])) {
        header('Content-Disposition: attachment; filename="' . (string) $response['body']['__file_name'] . '"');
    }
    echo (string) $response['body']['__raw'];
} else {
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode($response['body'], JSON_UNESCAPED_UNICODE);
}

$durationMs = (int) round((microtime(true) - $start) * 1000);
$logger->info('http_request', [
    'request_id' => $requestId,
    'method' => $method,
    'path' => $path,
    'status' => $response['status'],
    'duration_ms' => $durationMs,
]);
