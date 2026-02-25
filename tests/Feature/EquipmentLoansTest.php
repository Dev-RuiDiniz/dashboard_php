<?php

declare(strict_types=1);

require_once __DIR__ . '/../../src/Auth/JwtService.php';
require_once __DIR__ . '/../../src/Auth/UserStore.php';
require_once __DIR__ . '/../../src/Domain/CpfValidator.php';
require_once __DIR__ . '/../../src/Domain/SocialStore.php';
require_once __DIR__ . '/../../src/Domain/StreetStore.php';
require_once __DIR__ . '/../../src/Domain/DeliveryStore.php';
require_once __DIR__ . '/../../src/Domain/EquipmentStore.php';
require_once __DIR__ . '/../../src/Domain/SettingsStore.php';
require_once __DIR__ . '/../../src/Domain/EligibilityService.php';
require_once __DIR__ . '/../../src/Reports/ExportService.php';
require_once __DIR__ . '/../../src/Http/Kernel.php';

use App\Domain\DeliveryStore;
use App\Domain\EquipmentStore;
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

$social = new SocialStore('/tmp/social_store_test_s8.json');
$street = new StreetStore('/tmp/street_store_test_s8.json');
$delivery = new DeliveryStore('/tmp/delivery_store_test_s8.json');
$equipment = new EquipmentStore('/tmp/equipment_store_test_s8.json');
$social->reset(); $street->reset(); $delivery->reset(); $equipment->reset();
$kernel = new Kernel(socialStore: $social, streetStore: $street, deliveryStore: $delivery, equipmentStore: $equipment);
$env=['JWT_SECRET'=>'test-secret'];
$login=$kernel->handle('POST','/auth/login','req-login',[],['email'=>'operador@local','password'=>'operador123'],$env);
$h=['Authorization'=>'Bearer '.(string)$login['body']['access_token']];

$f=$kernel->handle('POST','/families','req-family',$h,['responsible_full_name'=>'Fam EQ','responsible_cpf'=>'529.982.247-25'],$env);
$familyId=(int)$f['body']['item']['id'];

$eq=$kernel->handle('POST','/equipment','req-eq',$h,['type'=>'cadeira de rodas','condition'=>'boa','notes'=>'n1'],$env);
assertTrue($eq['status']===201,'equipamento deve ser criado');
$eqId=(int)$eq['body']['item']['id'];

$loan=$kernel->handle('POST','/equipment/loans','req-loan',$h,['equipment_id'=>$eqId,'family_id'=>$familyId,'due_date'=>'2026-09-01'],$env);
assertTrue($loan['status']===201,'emprestimo deve ser criado');
$loanId=(int)$loan['body']['item']['id'];

$loanAgain=$kernel->handle('POST','/equipment/loans','req-loan2',$h,['equipment_id'=>$eqId,'family_id'=>$familyId,'due_date'=>'2026-09-01'],$env);
assertTrue($loanAgain['status']===409,'equipamento emprestado nao pode emprestar novamente');

$return=$kernel->handle('POST','/equipment/loans/'.$loanId.'/return','req-return',$h,['condition'=>'boa','notes'=>'ok'],$env);
assertTrue($return['status']===200,'devolucao deve funcionar');

$returnAgain=$kernel->handle('POST','/equipment/loans/'.$loanId.'/return','req-return2',$h,['condition'=>'boa','notes'=>'ok'],$env);
assertTrue($returnAgain['status']===409,'nao pode devolver emprestimo ja fechado');

$list=$kernel->handle('GET','/equipment/loans','req-list',$h,[],$env);
assertTrue($list['status']===200,'listagem emprestimos deve funcionar');
assertTrue(count($list['body']['items']??[])===1,'deve haver 1 emprestimo');

$social->reset(); $street->reset(); $delivery->reset(); $equipment->reset();
echo "OK: EquipmentLoansTest" . PHP_EOL;
