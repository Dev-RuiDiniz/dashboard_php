<?php

declare(strict_types=1);

require_once __DIR__ . '/../../src/Auth/JwtService.php';
require_once __DIR__ . '/../../src/Auth/UserStore.php';
require_once __DIR__ . '/../../src/Domain/CpfValidator.php';
require_once __DIR__ . '/../../src/Domain/SocialStore.php';
require_once __DIR__ . '/../../src/Domain/StreetStore.php';
require_once __DIR__ . '/../../src/Domain/DeliveryStore.php';
require_once __DIR__ . '/../../src/Domain/EquipmentStore.php';
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

$social = new SocialStore('/tmp/social_store_test_s6.json');
$street = new StreetStore('/tmp/street_store_test_s6.json');
$delivery = new DeliveryStore('/tmp/delivery_store_test_s6.json');
$social->reset(); $street->reset(); $delivery->reset();
$kernel = new Kernel(socialStore: $social, streetStore: $street, deliveryStore: $delivery);
$env=['JWT_SECRET'=>'test-secret'];
$login=$kernel->handle('POST','/auth/login','req-login',[],['email'=>'operador@local','password'=>'operador123'],$env);
$token=(string)$login['body']['access_token'];
$h=['Authorization'=>'Bearer '.$token];

$f=$kernel->handle('POST','/families','req-f',$h,['responsible_full_name'=>'Fam 1','responsible_cpf'=>'529.982.247-25'],$env);
$familyId=(int)$f['body']['item']['id'];

$e=$kernel->handle('POST','/deliveries/events','req-e',$h,['name'=>'Evento Maio','event_date'=>'2026-05-10'],$env);
assertTrue($e['status']===201,'evento deve ser criado');
$eventId=(int)$e['body']['item']['id'];

$i=$kernel->handle('POST','/deliveries/events/'.$eventId.'/invites','req-i',$h,['family_id'=>$familyId],$env);
assertTrue($i['status']===201,'convite deve ser criado');
assertTrue(strlen((string)($i['body']['item']['withdrawal_code']??''))===6,'codigo deve ter 6 chars');

$w1=$kernel->handle('POST','/deliveries/events/'.$eventId.'/withdrawals','req-w1',$h,['family_id'=>$familyId,'signature_accepted'=>true,'signature_name'=>'Assinante'],$env);
assertTrue($w1['status']===201,'primeira retirada deve funcionar');

$w2=$kernel->handle('POST','/deliveries/events/'.$eventId.'/withdrawals','req-w2',$h,['family_id'=>$familyId,'signature_accepted'=>true,'signature_name'=>'Assinante'],$env);
assertTrue($w2['status']===409,'segunda retirada no mes deve bloquear');

$e2=$kernel->handle('POST','/deliveries/events','req-e2',$h,['name'=>'Evento Junho','event_date'=>'2026-06-10'],$env);
$eventId2=(int)$e2['body']['item']['id'];
$w3=$kernel->handle('POST','/deliveries/events/'.$eventId2.'/withdrawals','req-w3',$h,['family_id'=>$familyId,'signature_accepted'=>false,'signature_name'=>''],$env);
assertTrue($w3['status']===422,'retirada sem assinatura deve falhar');

$social->reset(); $street->reset(); $delivery->reset();
echo "OK: DeliveryEventsRulesTest" . PHP_EOL;
