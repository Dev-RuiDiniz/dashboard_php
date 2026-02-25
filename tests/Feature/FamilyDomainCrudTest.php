<?php

declare(strict_types=1);

require_once __DIR__ . '/../../src/Auth/JwtService.php';
require_once __DIR__ . '/../../src/Auth/UserStore.php';
require_once __DIR__ . '/../../src/Domain/CpfValidator.php';
require_once __DIR__ . '/../../src/Domain/SocialStore.php';
require_once __DIR__ . '/../../src/Domain/StreetStore.php';
require_once __DIR__ . '/../../src/Domain/DeliveryStore.php';
require_once __DIR__ . '/../../src/Http/Kernel.php';

use App\Domain\SocialStore;
use App\Http\Kernel;

function assertTrue(bool $condition, string $message): void
{
    if (!$condition) {
        fwrite(STDERR, "Assertion failed: {$message}" . PHP_EOL);
        exit(1);
    }
}

$store = new SocialStore('/tmp/social_store_test.json');
$store->reset();
$kernel = new Kernel(socialStore: $store);
$env = ['JWT_SECRET' => 'test-secret'];

$login = $kernel->handle('POST', '/auth/login', 'req-login', [], ['email' => 'operador@local', 'password' => 'operador123'], $env);
assertTrue($login['status'] === 200, 'login operador deve retornar 200');
$token = (string) ($login['body']['access_token'] ?? '');
$headers = ['Authorization' => 'Bearer ' . $token];

$createFamily = $kernel->handle('POST', '/families', 'req-family-create', $headers, [
    'responsible_full_name' => 'Maria Silva',
    'responsible_cpf' => '529.982.247-25',
], $env);
assertTrue($createFamily['status'] === 201, 'create family deve retornar 201');
$familyId = (int) ($createFamily['body']['item']['id'] ?? 0);
assertTrue($familyId > 0, 'family id deve existir');

$duplicateCpf = $kernel->handle('POST', '/families', 'req-family-dup', $headers, [
    'responsible_full_name' => 'Outra Pessoa',
    'responsible_cpf' => '52998224725',
], $env);
assertTrue($duplicateCpf['status'] === 409, 'cpf duplicado deve retornar 409');

$badCpf = $kernel->handle('POST', '/families', 'req-family-badcpf', $headers, [
    'responsible_full_name' => 'CPF Inválido',
    'responsible_cpf' => '111.111.111-11',
], $env);
assertTrue($badCpf['status'] === 422, 'cpf inválido deve retornar 422');

$createDependent = $kernel->handle('POST', '/dependents', 'req-dep-create', $headers, [
    'family_id' => $familyId,
    'full_name' => 'Dependente 1',
], $env);
assertTrue($createDependent['status'] === 201, 'create dependent deve retornar 201');
$dependentId = (int) ($createDependent['body']['item']['id'] ?? 0);

$createChild = $kernel->handle('POST', '/children', 'req-child-create', $headers, [
    'family_id' => $familyId,
    'full_name' => 'Criança 1',
], $env);
assertTrue($createChild['status'] === 201, 'create child deve retornar 201');
$childId = (int) ($createChild['body']['item']['id'] ?? 0);

$listFamilies = $kernel->handle('GET', '/families', 'req-list-families', $headers, [], $env);
assertTrue($listFamilies['status'] === 200, 'list families deve retornar 200');
assertTrue(count($listFamilies['body']['items'] ?? []) === 1, 'deve haver 1 família');

$updateFamily = $kernel->handle('PUT', '/families/' . $familyId, 'req-family-update', $headers, [
    'responsible_full_name' => 'Maria Silva Atualizada',
    'responsible_cpf' => '52998224725',
], $env);
assertTrue($updateFamily['status'] === 200, 'update family deve retornar 200');

$deleteDependent = $kernel->handle('DELETE', '/dependents/' . $dependentId, 'req-dep-delete', $headers, [], $env);
assertTrue($deleteDependent['status'] === 200, 'delete dependent deve retornar 200');

$deleteChild = $kernel->handle('DELETE', '/children/' . $childId, 'req-child-delete', $headers, [], $env);
assertTrue($deleteChild['status'] === 200, 'delete child deve retornar 200');

$deleteFamily = $kernel->handle('DELETE', '/families/' . $familyId, 'req-family-delete', $headers, [], $env);
assertTrue($deleteFamily['status'] === 200, 'delete family deve retornar 200');

$readOnlyLogin = $kernel->handle('POST', '/auth/login', 'req-read-login', [], ['email' => 'leitura@local', 'password' => 'leitura123'], $env);
$readOnlyToken = (string) ($readOnlyLogin['body']['access_token'] ?? '');
$forbidden = $kernel->handle('POST', '/families', 'req-forbidden', ['Authorization' => 'Bearer ' . $readOnlyToken], [
    'responsible_full_name' => 'Sem Permissão',
    'responsible_cpf' => '12345678909',
], $env);
assertTrue($forbidden['status'] === 403, 'perfil leitura não pode escrever');

 $store->reset();

echo "OK: FamilyDomainCrudTest" . PHP_EOL;
