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
require_once __DIR__ . '/../../src/Domain/AuthThrottleStore.php';
require_once __DIR__ . '/../../src/Reports/ExportService.php';
require_once __DIR__ . '/../../src/Http/Kernel.php';

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

$social = new SocialStore('/tmp/social_store_test_s5.json');
$street = new StreetStore('/tmp/street_store_test_s5.json');
$social->reset();
$street->reset();
$kernel = new Kernel(socialStore: $social, streetStore: $street);
$env = ['JWT_SECRET' => 'test-secret'];

$login = $kernel->handle('POST', '/auth/login', 'req-login', [], ['email' => 'operador@local', 'password' => 'operador123'], $env);
$token = (string) ($login['body']['access_token'] ?? '');
$headers = ['Authorization' => 'Bearer ' . $token];

$withoutConsent = $kernel->handle('POST', '/street/people', 'req-street-noconsent', $headers, [
    'full_name' => 'Pessoa Sem Consentimento',
    'concluded' => true,
    'consent_accepted' => false,
    'signature_name' => '',
], $env);
assertTrue($withoutConsent['status'] === 422, 'conclusão sem consentimento deve falhar');

$withConsent = $kernel->handle('POST', '/street/people', 'req-street-consent', $headers, [
    'full_name' => 'Pessoa Com Consentimento',
    'concluded' => true,
    'consent_accepted' => true,
    'signature_name' => 'Pessoa Com Consentimento',
], $env);
assertTrue($withConsent['status'] === 201, 'conclusão com consentimento deve funcionar');
$personId = (int) ($withConsent['body']['item']['id'] ?? 0);

$referral = $kernel->handle('POST', '/street/referrals', 'req-referral', $headers, [
    'person_id' => $personId,
    'target' => 'CRAS',
], $env);
assertTrue($referral['status'] === 201, 'criar encaminhamento deve funcionar');
$referralId = (int) ($referral['body']['item']['id'] ?? 0);

$refStatus = $kernel->handle('POST', '/street/referrals/' . $referralId . '/status', 'req-ref-status', $headers, [
    'status' => 'concluido',
], $env);
assertTrue($refStatus['status'] === 200, 'atualização de status deve funcionar');
assertTrue(($refStatus['body']['item']['status'] ?? '') === 'concluido', 'status deve ser atualizado');

$readLogin = $kernel->handle('POST', '/auth/login', 'req-login-read', [], ['email' => 'leitura@local', 'password' => 'leitura123'], $env);
$readToken = (string) ($readLogin['body']['access_token'] ?? '');
$forbidden = $kernel->handle('POST', '/street/people', 'req-forbidden', ['Authorization' => 'Bearer ' . $readToken], [
    'full_name' => 'Sem permissão',
    'concluded' => false,
], $env);
assertTrue($forbidden['status'] === 403, 'perfil leitura não pode escrever no módulo street');

$social->reset();
$street->reset();

echo "OK: StreetLgpdReferralTest" . PHP_EOL;
