<?php

declare(strict_types=1);

require_once __DIR__ . '/../../src/Auth/JwtService.php';
require_once __DIR__ . '/../../src/Auth/UserStore.php';
require_once __DIR__ . '/../../src/Domain/CpfValidator.php';
require_once __DIR__ . '/../../src/Domain/SocialStore.php';
require_once __DIR__ . '/../../src/Domain/StreetStore.php';
require_once __DIR__ . '/../../src/Domain/DeliveryStore.php';
require_once __DIR__ . '/../../src/Reports/ExportService.php';
require_once __DIR__ . '/../../src/Http/Kernel.php';

use App\Domain\DeliveryStore;
use App\Domain\SocialStore;
use App\Domain\StreetStore;
use App\Http\Kernel;

function assertTrue(bool $condition, string $message): void
{
    if (!$condition) {
        fwrite(STDERR, "Assertion failed: {$message}" . PHP_EOL);
        exit(1);
    }
}

$social = new SocialStore('/tmp/social_store_test_s7.json');
$street = new StreetStore('/tmp/street_store_test_s7.json');
$delivery = new DeliveryStore('/tmp/delivery_store_test_s7.json');
$social->reset(); $street->reset(); $delivery->reset();
$kernel = new Kernel(socialStore: $social, streetStore: $street, deliveryStore: $delivery);
$env=['JWT_SECRET'=>'test-secret'];

$login=$kernel->handle('POST','/auth/login','req-login',[],['email'=>'operador@local','password'=>'operador123'],$env);
$token=(string)$login['body']['access_token'];
$h=['Authorization'=>'Bearer '.$token];

$kernel->handle('POST','/families','req-f1',$h,['responsible_full_name'=>'Maria Silva','responsible_cpf'=>'529.982.247-25'],$env);

$csv=$kernel->handle('GET','/reports/export.csv','req-csv',$h,[],$env);
assertTrue($csv['status']===200,'csv deve retornar 200');
assertTrue(str_contains((string)$csv['body']['__content_type'],'text/csv'),'content type csv');
assertTrue(str_contains((string)$csv['body']['__raw'],'responsible_full_name'),'csv deve conter header');

$xlsx=$kernel->handle('GET','/reports/export.xlsx','req-xlsx',$h,[],$env);
assertTrue($xlsx['status']===200,'xlsx deve retornar 200');
assertTrue(str_contains((string)$xlsx['body']['__content_type'],'spreadsheetml'),'content type xlsx');

$pdf=$kernel->handle('GET','/reports/export.pdf','req-pdf',$h,[],$env);
assertTrue($pdf['status']===200,'pdf deve retornar 200');
assertTrue((string)$pdf['body']['__content_type']==='application/pdf','content type pdf');
assertTrue(str_contains((string)$pdf['body']['__raw'],'RELATORIO DE FAMILIAS'),'pdf deve conter titulo');

$social->reset(); $street->reset(); $delivery->reset();
echo "OK: ReportsExportTest" . PHP_EOL;
