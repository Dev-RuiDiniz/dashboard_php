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
use App\Domain\SettingsStore;
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

$social = new SocialStore('/tmp/social_store_test_s9.json');
$street = new StreetStore('/tmp/street_store_test_s9.json');
$delivery = new DeliveryStore('/tmp/delivery_store_test_s9.json');
$equipment = new EquipmentStore('/tmp/equipment_store_test_s9.json');
$settings = new SettingsStore('/tmp/settings_store_test_s9.json');
$social->reset(); $street->reset(); $delivery->reset(); $equipment->reset(); $settings->reset();
$kernel = new Kernel(socialStore: $social, streetStore: $street, deliveryStore: $delivery, equipmentStore: $equipment, settingsStore: $settings);
$env=['JWT_SECRET'=>'test-secret'];
$login=$kernel->handle('POST','/auth/login','req-login',[],['email'=>'operador@local','password'=>'operador123'],$env);
$h=['Authorization'=>'Bearer '.(string)$login['body']['access_token']];

$kernel->handle('POST','/families','req-f',$h,['responsible_full_name'=>'Fam 1','responsible_cpf'=>'529.982.247-25'],$env);
$summary=$kernel->handle('GET','/reports/summary','req-summary',$h,[],$env);
assertTrue($summary['status']===200,'summary deve retornar 200');
assertTrue((int)($summary['body']['families_total'] ?? 0) >= 1,'summary deve contabilizar familias');

$upd=$kernel->handle('PUT','/settings/eligibility','req-upd',$h,[
 'max_deliveries_per_month'=>2,
 'min_months_since_last_delivery'=>3,
 'min_vulnerability_score'=>4,
 'require_documentation'=>true,
],$env);
assertTrue($upd['status']===200,'update settings deve retornar 200');

$get=$kernel->handle('GET','/settings/eligibility','req-get',$h,[],$env);
assertTrue($get['status']===200,'get settings deve retornar 200');
assertTrue((bool)($get['body']['item']['require_documentation'] ?? false)===true,'setting deve persistir');

$elig1=$kernel->handle('POST','/eligibility/check','req-elig1',$h,[
 'deliveries_this_month'=>0,
 'months_since_last_delivery'=>3,
 'vulnerability_score'=>5,
 'has_documentation'=>true,
],$env);
assertTrue(($elig1['body']['item']['eligible'] ?? false)===true,'cenario deve ser elegivel');

$elig2=$kernel->handle('POST','/eligibility/check','req-elig2',$h,[
 'deliveries_this_month'=>2,
 'months_since_last_delivery'=>0,
 'vulnerability_score'=>1,
 'has_documentation'=>false,
],$env);
assertTrue(($elig2['body']['item']['eligible'] ?? true)===false,'cenario deve ser inelegivel');
assertTrue(count($elig2['body']['item']['reasons'] ?? [])>=1,'deve listar motivos');

$social->reset(); $street->reset(); $delivery->reset(); $equipment->reset(); $settings->reset();
echo "OK: ReportsEligibilitySettingsTest" . PHP_EOL;
