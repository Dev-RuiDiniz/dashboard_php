<?php

declare(strict_types=1);

namespace App\Http;

use App\Audit\AuditLogger;
use App\Auth\JwtService;
use App\Auth\UserStore;
use App\Domain\CpfValidator;
use App\Domain\SocialStore;
use App\Domain\StreetStore;
use App\Domain\DeliveryStore;
use App\Reports\ExportService;
use App\Domain\EquipmentStore;
use App\Domain\SettingsStore;
use App\Domain\EligibilityService;
use App\Domain\AuthThrottleStore;
use App\Domain\AuthResetTokenStore;

final class Kernel
{
    public function __construct(
        private ?JwtService $jwtService = null,
        private ?UserStore $userStore = null,
        private ?AuditLogger $auditLogger = null,
        private ?SocialStore $socialStore = null,
        private ?CpfValidator $cpfValidator = null,
        private ?StreetStore $streetStore = null,
        private ?DeliveryStore $deliveryStore = null,
        private ?ExportService $exportService = null,
        private ?EquipmentStore $equipmentStore = null,
        private ?SettingsStore $settingsStore = null,
        private ?EligibilityService $eligibilityService = null,
        private ?AuthThrottleStore $authThrottleStore = null,
        private ?AuthResetTokenStore $authResetTokenStore = null,
    ) {
        $this->jwtService = $this->jwtService ?? new JwtService();
        $this->userStore = $this->userStore ?? new UserStore();
        $this->socialStore = $this->socialStore ?? new SocialStore();
        $this->cpfValidator = $this->cpfValidator ?? new CpfValidator();
        $this->streetStore = $this->streetStore ?? new StreetStore();
        $this->deliveryStore = $this->deliveryStore ?? new DeliveryStore();
        $this->exportService = $this->exportService ?? new ExportService();
        $this->equipmentStore = $this->equipmentStore ?? new EquipmentStore();
        $this->settingsStore = $this->settingsStore ?? new SettingsStore();
        $this->eligibilityService = $this->eligibilityService ?? new EligibilityService();
        $this->authThrottleStore = $this->authThrottleStore ?? new AuthThrottleStore();
        $this->authResetTokenStore = $this->authResetTokenStore ?? new AuthResetTokenStore();
    }

    /**
     * @param array<string, string> $headers
     * @param array<string, mixed> $payload
     * @param array<string, mixed> $env
     * @return array{status:int, body:array<string,mixed>}
     */
    public function handle(string $method, string $path, string $requestId, array $headers = [], array $payload = [], array $env = []): array
    {
        if ($method === 'GET' && $path === '/health') {
            return ['status' => 200, 'body' => ['status' => 'ok', 'service' => 'dashboard_php', 'request_id' => $requestId]];
        }
        if ($method === 'GET' && $path === '/ready') {
            $isReady = ($env['APP_READY'] ?? getenv('APP_READY') ?: 'true') !== 'false';
            return ['status' => $isReady ? 200 : 503, 'body' => ['status' => $isReady ? 'ready' : 'not_ready', 'service' => 'dashboard_php', 'request_id' => $requestId]];
        }

        if ($method === 'POST' && $path === '/auth/login') {
            return $this->login($requestId, $payload, $env);
        }
        if ($method === 'POST' && $path === '/auth/forgot') {
            return $this->forgotPassword($requestId, $payload, $env);
        }
        if ($method === 'POST' && $path === '/auth/reset') {
            return $this->resetPassword($requestId, $payload, $env);
        }
        if ($method === 'GET' && $path === '/me') {
            return $this->me($requestId, $headers, $env);
        }
        if ($method === 'POST' && $path === '/auth/logout') {
            $this->audit('auth.logout', $requestId, []);
            return ['status' => 200, 'body' => ['status' => 'logged_out', 'request_id' => $requestId]];
        }

        $permission = $this->resolvePermission($method, $path);
        if ($permission !== null) {
            $authz = $this->requirePermission($requestId, $headers, $env, $permission);
            if (isset($authz['response'])) {
                return $authz['response'];
            }
        }
        if ($method === 'GET' && $path === '/admin/ping') {
            $auth = $this->requireAuth($requestId, $headers, $env);
            if (isset($auth['response'])) {
                return $auth['response'];
            }
            if (!$this->userStore->hasPermission($auth['user'], 'admin.ping')) {
                $this->audit('auth.forbidden', $requestId, ['path' => '/admin/ping']);
                return ['status' => 403, 'body' => ['error' => 'forbidden', 'request_id' => $requestId]];
            }
            return ['status' => 200, 'body' => ['status' => 'ok', 'scope' => 'admin', 'request_id' => $requestId]];
        }

        // Sprint 4: families/dependents/children
        if ($path === '/families' && $method === 'GET') {
            $auth = $this->requireAuth($requestId, $headers, $env);
            if (isset($auth['response'])) {
                return $auth['response'];
            }
            return ['status' => 200, 'body' => ['items' => $this->socialStore->listFamilies(), 'request_id' => $requestId]];
        }
        if ($path === '/families' && $method === 'POST') {
            $auth = $this->requireWriter($requestId, $headers, $env);
            if (isset($auth['response'])) {
                return $auth['response'];
            }
            $name = trim((string) ($payload['responsible_full_name'] ?? ''));
            $cpf = $this->cpfValidator->normalize((string) ($payload['responsible_cpf'] ?? ''));
            if ($name === '' || !$this->cpfValidator->isValid($cpf)) {
                return ['status' => 422, 'body' => ['error' => 'invalid_payload', 'request_id' => $requestId]];
            }
            if ($this->socialStore->familyCpfExists($cpf)) {
                return ['status' => 409, 'body' => ['error' => 'duplicate_cpf', 'request_id' => $requestId]];
            }
            $family = $this->socialStore->createFamily($name, $cpf);
            $this->audit('family.created', $requestId, ['family_id' => (string) $family['id']]);
            return ['status' => 201, 'body' => ['item' => $family, 'request_id' => $requestId]];
        }
        if (preg_match('#^/families/(\d+)$#', $path, $match) === 1) {
            $familyId = (int) $match[1];
            if ($method === 'GET') {
                $auth = $this->requireAuth($requestId, $headers, $env);
                if (isset($auth['response'])) {
                    return $auth['response'];
                }
                $family = $this->socialStore->getFamily($familyId);
                if (!$family) {
                    return ['status' => 404, 'body' => ['error' => 'family_not_found', 'request_id' => $requestId]];
                }
                return ['status' => 200, 'body' => ['item' => $family, 'request_id' => $requestId]];
            }
            if ($method === 'PUT') {
                $auth = $this->requireWriter($requestId, $headers, $env);
                if (isset($auth['response'])) {
                    return $auth['response'];
                }
                $name = trim((string) ($payload['responsible_full_name'] ?? ''));
                $cpf = $this->cpfValidator->normalize((string) ($payload['responsible_cpf'] ?? ''));
                if ($name === '' || !$this->cpfValidator->isValid($cpf)) {
                    return ['status' => 422, 'body' => ['error' => 'invalid_payload', 'request_id' => $requestId]];
                }
                if ($this->socialStore->familyCpfExists($cpf, $familyId)) {
                    return ['status' => 409, 'body' => ['error' => 'duplicate_cpf', 'request_id' => $requestId]];
                }
                $updated = $this->socialStore->updateFamily($familyId, $name, $cpf);
                if (!$updated) {
                    return ['status' => 404, 'body' => ['error' => 'family_not_found', 'request_id' => $requestId]];
                }
                $this->audit('family.updated', $requestId, ['family_id' => (string) $familyId]);
                return ['status' => 200, 'body' => ['item' => $updated, 'request_id' => $requestId]];
            }
            if ($method === 'DELETE') {
                $auth = $this->requireWriter($requestId, $headers, $env);
                if (isset($auth['response'])) {
                    return $auth['response'];
                }
                if (!$this->socialStore->deleteFamily($familyId)) {
                    return ['status' => 404, 'body' => ['error' => 'family_not_found', 'request_id' => $requestId]];
                }
                $this->audit('family.deleted', $requestId, ['family_id' => (string) $familyId]);
                return ['status' => 200, 'body' => ['status' => 'deleted', 'request_id' => $requestId]];
            }
        }
        if ($path === '/dependents' && $method === 'GET') {
            $auth = $this->requireAuth($requestId, $headers, $env);
            if (isset($auth['response'])) {
                return $auth['response'];
            }
            return ['status' => 200, 'body' => ['items' => $this->socialStore->listDependents(), 'request_id' => $requestId]];
        }
        if ($path === '/dependents' && $method === 'POST') {
            $auth = $this->requireWriter($requestId, $headers, $env);
            if (isset($auth['response'])) {
                return $auth['response'];
            }
            $familyId = (int) ($payload['family_id'] ?? 0);
            $name = trim((string) ($payload['full_name'] ?? ''));
            if ($familyId <= 0 || $name === '') {
                return ['status' => 422, 'body' => ['error' => 'invalid_payload', 'request_id' => $requestId]];
            }
            $item = $this->socialStore->createDependent($familyId, $name);
            if (!$item) {
                return ['status' => 404, 'body' => ['error' => 'family_not_found', 'request_id' => $requestId]];
            }
            $this->audit('dependent.created', $requestId, ['dependent_id' => (string) $item['id']]);
            return ['status' => 201, 'body' => ['item' => $item, 'request_id' => $requestId]];
        }
        if (preg_match('#^/dependents/(\d+)$#', $path, $match) === 1 && $method === 'DELETE') {
            $auth = $this->requireWriter($requestId, $headers, $env);
            if (isset($auth['response'])) {
                return $auth['response'];
            }
            if (!$this->socialStore->deleteDependent((int) $match[1])) {
                return ['status' => 404, 'body' => ['error' => 'dependent_not_found', 'request_id' => $requestId]];
            }
            $this->audit('dependent.deleted', $requestId, ['dependent_id' => $match[1]]);
            return ['status' => 200, 'body' => ['status' => 'deleted', 'request_id' => $requestId]];
        }
        if ($path === '/children' && $method === 'GET') {
            $auth = $this->requireAuth($requestId, $headers, $env);
            if (isset($auth['response'])) {
                return $auth['response'];
            }
            return ['status' => 200, 'body' => ['items' => $this->socialStore->listChildren(), 'request_id' => $requestId]];
        }
        if ($path === '/children' && $method === 'POST') {
            $auth = $this->requireWriter($requestId, $headers, $env);
            if (isset($auth['response'])) {
                return $auth['response'];
            }
            $familyId = (int) ($payload['family_id'] ?? 0);
            $name = trim((string) ($payload['full_name'] ?? ''));
            if ($familyId <= 0 || $name === '') {
                return ['status' => 422, 'body' => ['error' => 'invalid_payload', 'request_id' => $requestId]];
            }
            $item = $this->socialStore->createChild($familyId, $name);
            if (!$item) {
                return ['status' => 404, 'body' => ['error' => 'family_not_found', 'request_id' => $requestId]];
            }
            $this->audit('child.created', $requestId, ['child_id' => (string) $item['id']]);
            return ['status' => 201, 'body' => ['item' => $item, 'request_id' => $requestId]];
        }
        if (preg_match('#^/children/(\d+)$#', $path, $match) === 1 && $method === 'DELETE') {
            $auth = $this->requireWriter($requestId, $headers, $env);
            if (isset($auth['response'])) {
                return $auth['response'];
            }
            if (!$this->socialStore->deleteChild((int) $match[1])) {
                return ['status' => 404, 'body' => ['error' => 'child_not_found', 'request_id' => $requestId]];
            }
            $this->audit('child.deleted', $requestId, ['child_id' => $match[1]]);
            return ['status' => 200, 'body' => ['status' => 'deleted', 'request_id' => $requestId]];
        }

        // Sprint 5: street + referrals + consent
        if ($path === '/street/people' && $method === 'GET') {
            $auth = $this->requireAuth($requestId, $headers, $env);
            if (isset($auth['response'])) {
                return $auth['response'];
            }
            return ['status' => 200, 'body' => ['items' => $this->streetStore->listPeople(), 'request_id' => $requestId]];
        }

        if ($path === '/street/people' && $method === 'POST') {
            $auth = $this->requireWriter($requestId, $headers, $env);
            if (isset($auth['response'])) {
                return $auth['response'];
            }

            $name = trim((string) ($payload['full_name'] ?? ''));
            $concluded = (bool) ($payload['concluded'] ?? false);
            $consentAccepted = (bool) ($payload['consent_accepted'] ?? false);
            $signatureName = trim((string) ($payload['signature_name'] ?? ''));

            if ($name === '') {
                return ['status' => 422, 'body' => ['error' => 'invalid_payload', 'request_id' => $requestId]];
            }
            if ($concluded && (!$consentAccepted || $signatureName === '')) {
                return ['status' => 422, 'body' => ['error' => 'consent_required', 'request_id' => $requestId]];
            }

            $person = $this->streetStore->createPerson($name, $concluded, $consentAccepted, $signatureName);
            $this->audit('street.person.created', $requestId, ['person_id' => (string) $person['id']]);
            return ['status' => 201, 'body' => ['item' => $person, 'request_id' => $requestId]];
        }

        if ($path === '/street/referrals' && $method === 'POST') {
            $auth = $this->requireWriter($requestId, $headers, $env);
            if (isset($auth['response'])) {
                return $auth['response'];
            }

            $personId = (int) ($payload['person_id'] ?? 0);
            $target = trim((string) ($payload['target'] ?? ''));
            if ($personId <= 0 || $target === '') {
                return ['status' => 422, 'body' => ['error' => 'invalid_payload', 'request_id' => $requestId]];
            }

            $referral = $this->streetStore->createReferral($personId, $target);
            if (!$referral) {
                return ['status' => 404, 'body' => ['error' => 'person_not_found', 'request_id' => $requestId]];
            }

            $this->audit('street.referral.created', $requestId, ['referral_id' => (string) $referral['id']]);
            return ['status' => 201, 'body' => ['item' => $referral, 'request_id' => $requestId]];
        }

        if (preg_match('#^/street/referrals/(\d+)/status$#', $path, $match) === 1 && $method === 'POST') {
            $auth = $this->requireWriter($requestId, $headers, $env);
            if (isset($auth['response'])) {
                return $auth['response'];
            }

            $status = trim((string) ($payload['status'] ?? ''));
            if ($status === '') {
                return ['status' => 422, 'body' => ['error' => 'invalid_payload', 'request_id' => $requestId]];
            }

            $updated = $this->streetStore->updateReferralStatus((int) $match[1], $status);
            if (!$updated) {
                return ['status' => 404, 'body' => ['error' => 'referral_not_found', 'request_id' => $requestId]];
            }

            $this->audit('street.referral.status_updated', $requestId, ['referral_id' => $match[1], 'status' => $status]);
            return ['status' => 200, 'body' => ['item' => $updated, 'request_id' => $requestId]];
        }

        



        // Sprint 9: reports summary + eligibility + settings
        if ($path === '/reports/summary' && $method === 'GET') {
            $auth = $this->requireAuth($requestId, $headers, $env);
            if (isset($auth['response'])) { return $auth['response']; }

            return ['status'=>200,'body'=>[
                'families_total' => count($this->socialStore->listFamilies()),
                'street_people_total' => count($this->streetStore->listPeople()),
                'events_total' => count($this->deliveryStore->listEvents()),
                'equipments_total' => count($this->equipmentStore->listEquipments()),
                'open_loans_total' => count(array_values(array_filter($this->equipmentStore->listLoans(), static fn($l) => ($l['status'] ?? '') === 'aberto'))),
                'request_id' => $requestId,
            ]];
        }

        if ($path === '/settings/eligibility' && $method === 'GET') {
            $auth = $this->requireAuth($requestId, $headers, $env);
            if (isset($auth['response'])) { return $auth['response']; }
            return ['status'=>200,'body'=>['item'=>$this->settingsStore->get(),'request_id'=>$requestId]];
        }

        if ($path === '/settings/eligibility' && $method === 'PUT') {
            $auth = $this->requireWriter($requestId, $headers, $env);
            if (isset($auth['response'])) { return $auth['response']; }
            $updated = $this->settingsStore->update([
                'max_deliveries_per_month' => (int)($payload['max_deliveries_per_month'] ?? 1),
                'min_months_since_last_delivery' => (int)($payload['min_months_since_last_delivery'] ?? 1),
                'min_vulnerability_score' => (int)($payload['min_vulnerability_score'] ?? 1),
                'require_documentation' => (bool)($payload['require_documentation'] ?? false),
            ]);
            $this->audit('settings.eligibility.updated', $requestId, []);
            return ['status'=>200,'body'=>['item'=>$updated,'request_id'=>$requestId]];
        }

        if ($path === '/eligibility/check' && $method === 'POST') {
            $auth = $this->requireAuth($requestId, $headers, $env);
            if (isset($auth['response'])) { return $auth['response']; }
            $rules = $this->settingsStore->get();
            $result = $this->eligibilityService->evaluate($rules, $payload);
            return ['status'=>200,'body'=>['item'=>$result,'request_id'=>$requestId]];
        }

        // Sprint 8: equipment + loans
        if ($path === '/equipment' && $method === 'GET') {
            $auth = $this->requireAuth($requestId, $headers, $env);
            if (isset($auth['response'])) { return $auth['response']; }
            return ['status'=>200,'body'=>['items'=>$this->equipmentStore->listEquipments(),'request_id'=>$requestId]];
        }

        if ($path === '/equipment' && $method === 'POST') {
            $auth = $this->requireWriter($requestId, $headers, $env);
            if (isset($auth['response'])) { return $auth['response']; }
            $type=trim((string)($payload['type']??''));
            $condition=trim((string)($payload['condition']??''));
            $notes=trim((string)($payload['notes']??''));
            if ($type==='' || $condition==='') return ['status'=>422,'body'=>['error'=>'invalid_payload','request_id'=>$requestId]];
            $e=$this->equipmentStore->createEquipment($type,$condition,$notes);
            $this->audit('equipment.created',$requestId,['equipment_id'=>(string)$e['id']]);
            return ['status'=>201,'body'=>['item'=>$e,'request_id'=>$requestId]];
        }

        if (preg_match('#^/equipment/(\d+)$#',$path,$m)===1 && $method==='PUT') {
            $auth = $this->requireWriter($requestId, $headers, $env);
            if (isset($auth['response'])) { return $auth['response']; }
            $status=trim((string)($payload['status']??''));
            $condition=trim((string)($payload['condition']??''));
            $notes=trim((string)($payload['notes']??''));
            $u=$this->equipmentStore->updateEquipment((int)$m[1],$status,$condition,$notes);
            if (!$u) return ['status'=>404,'body'=>['error'=>'equipment_not_found','request_id'=>$requestId]];
            if (isset($u['error'])&&$u['error']==='invalid_status') return ['status'=>422,'body'=>['error'=>'invalid_status','request_id'=>$requestId]];
            $this->audit('equipment.updated',$requestId,['equipment_id'=>$m[1]]);
            return ['status'=>200,'body'=>['item'=>$u,'request_id'=>$requestId]];
        }

        if ($path === '/equipment/loans' && $method === 'GET') {
            $auth = $this->requireAuth($requestId, $headers, $env);
            if (isset($auth['response'])) { return $auth['response']; }
            return ['status'=>200,'body'=>['items'=>$this->equipmentStore->listLoans(),'request_id'=>$requestId]];
        }

        if ($path === '/equipment/loans' && $method === 'POST') {
            $auth = $this->requireWriter($requestId, $headers, $env);
            if (isset($auth['response'])) { return $auth['response']; }
            $equipmentId=(int)($payload['equipment_id']??0);
            $familyId=(int)($payload['family_id']??0);
            $dueDate=trim((string)($payload['due_date']??''));
            if ($equipmentId<=0 || $familyId<=0 || !preg_match('/^\d{4}-\d{2}-\d{2}$/',$dueDate)) {
                return ['status'=>422,'body'=>['error'=>'invalid_payload','request_id'=>$requestId]];
            }
            $loan=$this->equipmentStore->createLoan($equipmentId,$familyId,$dueDate);
            if (!$loan) return ['status'=>404,'body'=>['error'=>'equipment_not_found','request_id'=>$requestId]];
            if (isset($loan['error'])&&$loan['error']==='equipment_unavailable') return ['status'=>409,'body'=>['error'=>'equipment_unavailable','request_id'=>$requestId]];
            $this->audit('equipment.loan.created',$requestId,['loan_id'=>(string)$loan['id']]);
            return ['status'=>201,'body'=>['item'=>$loan,'request_id'=>$requestId]];
        }

        if (preg_match('#^/equipment/loans/(\d+)/return$#',$path,$m)===1 && $method==='POST') {
            $auth = $this->requireWriter($requestId, $headers, $env);
            if (isset($auth['response'])) { return $auth['response']; }
            $condition=trim((string)($payload['condition']??''));
            $notes=trim((string)($payload['notes']??''));
            if ($condition==='') return ['status'=>422,'body'=>['error'=>'invalid_payload','request_id'=>$requestId]];
            $loan=$this->equipmentStore->returnLoan((int)$m[1],$condition,$notes);
            if (!$loan) return ['status'=>404,'body'=>['error'=>'loan_not_found','request_id'=>$requestId]];
            if (isset($loan['error'])&&$loan['error']==='loan_closed') return ['status'=>409,'body'=>['error'=>'loan_already_closed','request_id'=>$requestId]];
            $this->audit('equipment.loan.returned',$requestId,['loan_id'=>$m[1]]);
            return ['status'=>200,'body'=>['item'=>$loan,'request_id'=>$requestId]];
        }

        // Sprint 7: exports
        if (in_array($path, ['/reports/export.csv', '/reports/export.xlsx', '/reports/export.pdf'], true) && $method === 'GET') {
            $auth = $this->requireAuth($requestId, $headers, $env);
            if (isset($auth['response'])) { return $auth['response']; }

            $families = $this->socialStore->listFamilies();
            if ($path === '/reports/export.csv') {
                $raw = $this->exportService->buildCsv($families);
                return ['status'=>200,'body'=>['__raw'=>$raw,'__content_type'=>'text/csv; charset=utf-8','__file_name'=>'families.csv','request_id'=>$requestId]];
            }
            if ($path === '/reports/export.xlsx') {
                $raw = $this->exportService->buildXlsx($families);
                return ['status'=>200,'body'=>['__raw'=>$raw,'__content_type'=>'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet','__file_name'=>'families.xlsx','request_id'=>$requestId]];
            }
            $raw = $this->exportService->buildPdf($families);
            return ['status'=>200,'body'=>['__raw'=>$raw,'__content_type'=>'application/pdf','__file_name'=>'families.pdf','request_id'=>$requestId]];
        }

        // Sprint 6: deliveries/events
        if ($path === '/deliveries/events' && $method === 'GET') {
            $auth = $this->requireAuth($requestId, $headers, $env);
            if (isset($auth['response'])) { return $auth['response']; }
            return ['status' => 200, 'body' => ['items' => $this->deliveryStore->listEvents(), 'request_id' => $requestId]];
        }

        if ($path === '/deliveries/events' && $method === 'POST') {
            $auth = $this->requireWriter($requestId, $headers, $env);
            if (isset($auth['response'])) { return $auth['response']; }
            $name = trim((string)($payload['name'] ?? ''));
            $eventDate = trim((string)($payload['event_date'] ?? ''));
            if ($name === '' || !preg_match('/^\d{4}-\d{2}-\d{2}$/', $eventDate)) {
                return ['status'=>422,'body'=>['error'=>'invalid_payload','request_id'=>$requestId]];
            }
            $event = $this->deliveryStore->createEvent($name, $eventDate);
            $this->audit('delivery.event.created', $requestId, ['event_id'=>(string)$event['id']]);
            return ['status'=>201,'body'=>['item'=>$event,'request_id'=>$requestId]];
        }

        if (preg_match('#^/deliveries/events/(\d+)/invites$#', $path, $m) === 1 && $method === 'POST') {
            $auth = $this->requireWriter($requestId, $headers, $env);
            if (isset($auth['response'])) { return $auth['response']; }
            $familyId = (int)($payload['family_id'] ?? 0);
            if ($familyId <= 0) return ['status'=>422,'body'=>['error'=>'invalid_payload','request_id'=>$requestId]];
            $invite = $this->deliveryStore->inviteFamily((int)$m[1], $familyId);
            if (!$invite) return ['status'=>404,'body'=>['error'=>'event_not_found','request_id'=>$requestId]];
            $this->audit('delivery.invite.created', $requestId, ['invite_id'=>(string)$invite['id']]);
            return ['status'=>201,'body'=>['item'=>$invite,'request_id'=>$requestId]];
        }

        if (preg_match('#^/deliveries/events/(\d+)/withdrawals$#', $path, $m) === 1 && $method === 'POST') {
            $auth = $this->requireWriter($requestId, $headers, $env);
            if (isset($auth['response'])) { return $auth['response']; }
            $familyId = (int)($payload['family_id'] ?? 0);
            $signatureAccepted = (bool)($payload['signature_accepted'] ?? false);
            $signatureName = trim((string)($payload['signature_name'] ?? ''));
            if ($familyId <= 0) return ['status'=>422,'body'=>['error'=>'invalid_payload','request_id'=>$requestId]];
            $w = $this->deliveryStore->registerWithdrawal((int)$m[1], $familyId, $signatureAccepted, $signatureName);
            if (!$w) return ['status'=>404,'body'=>['error'=>'event_not_found','request_id'=>$requestId]];
            if (isset($w['error']) && $w['error']==='duplicate_month') return ['status'=>409,'body'=>['error'=>'duplicate_month_withdrawal','request_id'=>$requestId]];
            if (isset($w['error']) && $w['error']==='signature_required') return ['status'=>422,'body'=>['error'=>'signature_required','request_id'=>$requestId]];
            $this->audit('delivery.withdrawal.registered', $requestId, ['withdrawal_id'=>(string)$w['id']]);
            return ['status'=>201,'body'=>['item'=>$w,'request_id'=>$requestId]];
        }


        // Sprint 24: visitas e pendências
        if ($path === '/visits' && $method === 'GET') {
            $status = trim((string) ($payload['status'] ?? ''));
            if ($status !== '' && !in_array($status, ['pendente', 'concluida', 'cancelada'], true)) {
                return ['status' => 422, 'body' => ['error' => 'invalid_status', 'request_id' => $requestId]];
            }
            return ['status' => 200, 'body' => ['items' => $this->socialStore->listVisits($status !== '' ? $status : null), 'request_id' => $requestId]];
        }

        if ($path === '/visits' && $method === 'POST') {
            $personId = (int) ($payload['person_id'] ?? 0);
            $familyIdRaw = $payload['family_id'] ?? null;
            $familyId = is_numeric($familyIdRaw) ? (int) $familyIdRaw : null;
            $scheduledFor = trim((string) ($payload['scheduled_for'] ?? ''));
            $notes = trim((string) ($payload['notes'] ?? ''));
            if ($personId <= 0 || !preg_match('/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/', $scheduledFor)) {
                return ['status' => 422, 'body' => ['error' => 'invalid_payload', 'request_id' => $requestId]];
            }
            $visit = $this->socialStore->createVisit($personId, $familyId, $scheduledFor, $notes);
            if (!$visit) {
                return ['status' => 404, 'body' => ['error' => 'visit_not_created', 'request_id' => $requestId]];
            }
            $this->audit('visit.created', $requestId, ['visit_id' => (string) $visit['id']]);
            return ['status' => 201, 'body' => ['item' => $visit, 'request_id' => $requestId]];
        }

        if (preg_match('#^/visits/(\d+)/complete$#', $path, $m) === 1 && $method === 'POST') {
            $completedAt = trim((string) ($payload['completed_at'] ?? ''));
            if ($completedAt === '') {
                $completedAt = gmdate('Y-m-d H:i:s');
            }
            if (!preg_match('/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/', $completedAt)) {
                return ['status' => 422, 'body' => ['error' => 'invalid_payload', 'request_id' => $requestId]];
            }
            $visit = $this->socialStore->completeVisit((int) $m[1], $completedAt);
            if (!$visit) {
                return ['status' => 404, 'body' => ['error' => 'visit_not_found', 'request_id' => $requestId]];
            }
            $this->audit('visit.completed', $requestId, ['visit_id' => (string) $m[1]]);
            return ['status' => 200, 'body' => ['item' => $visit, 'request_id' => $requestId]];
        }

        if (!in_array($method, ['GET', 'POST', 'PUT', 'DELETE'], true)) {
            return ['status' => 405, 'body' => ['error' => 'method_not_allowed', 'request_id' => $requestId]];
        }
        return ['status' => 404, 'body' => ['error' => 'not_found', 'request_id' => $requestId]];
    }

    /** @param array<string,mixed> $payload @param array<string,mixed> $env */
    private function login(string $requestId, array $payload, array $env): array
    {
        $email = (string) ($payload['email'] ?? '');
        $password = (string) ($payload['password'] ?? '');

        if ($this->authThrottleStore->isBlocked($email)) {
            $this->audit('auth.login_blocked', $requestId, ['email' => $email]);
            return ['status' => 429, 'body' => ['error' => 'too_many_attempts', 'request_id' => $requestId]];
        }

        $user = $this->userStore->authenticate($email, $password);
        if (!$user) {
            $state = $this->authThrottleStore->registerFailure($email);
            $this->audit('auth.login_failed', $requestId, ['email' => $email, 'attempts' => (string) $state['attempts']]);
            if (($state['blocked'] ?? false) === true) {
                return ['status' => 429, 'body' => ['error' => 'too_many_attempts', 'request_id' => $requestId]];
            }
            return ['status' => 401, 'body' => ['error' => 'invalid_credentials', 'request_id' => $requestId]];
        }

        $this->authThrottleStore->clear($email);
        $secret = (string) ($env['JWT_SECRET'] ?? getenv('JWT_SECRET') ?: 'dev-secret');
        $token = $this->jwtService->issueToken((string) $user['email'], $secret);
        $this->audit('auth.login_success', $requestId, ['user_email' => (string) $user['email']]);
        return ['status' => 200, 'body' => ['access_token' => $token, 'token_type' => 'bearer', 'request_id' => $requestId]];
    }

    /** @param array<string,mixed> $payload @param array<string,mixed> $env */
    private function forgotPassword(string $requestId, array $payload, array $env): array
    {
        $email = trim((string) ($payload['email'] ?? ''));
        $expiresIn = (int) ($env['RESET_TOKEN_TTL_SECONDS'] ?? getenv('RESET_TOKEN_TTL_SECONDS') ?: 3600);
        $nowTs = (int) ($env['NOW_TS'] ?? time());

        if ($email !== '') {
            $knownUser = $this->userStore->findByEmail($email);
            if ($knownUser !== null) {
                $this->authResetTokenStore->purgeExpired($nowTs);
                $token = $this->authResetTokenStore->issueToken($email, $nowTs + $expiresIn, $nowTs);
                $this->audit('auth.password_reset_requested', $requestId, ['email' => $email]);
                $debugTokenEnabled = (($env['DEBUG_PASSWORD_RESET_TOKEN'] ?? getenv('DEBUG_PASSWORD_RESET_TOKEN') ?: 'false') === 'true');
                if ($debugTokenEnabled) {
                    return ['status' => 200, 'body' => ['status' => 'reset_requested', 'request_id' => $requestId, 'reset_token' => $token, 'expires_in' => $expiresIn]];
                }
            }
        }

        return ['status' => 200, 'body' => ['status' => 'reset_requested', 'request_id' => $requestId]];
    }

    /** @param array<string,mixed> $payload @param array<string,mixed> $env */
    private function resetPassword(string $requestId, array $payload, array $env): array
    {
        $token = trim((string) ($payload['token'] ?? ''));
        $newPassword = (string) ($payload['new_password'] ?? '');
        $nowTs = (int) ($env['NOW_TS'] ?? time());

        if ($token === '' || strlen($newPassword) < 8) {
            return ['status' => 422, 'body' => ['error' => 'invalid_payload', 'request_id' => $requestId]];
        }

        $email = $this->authResetTokenStore->consumeToken($token, $nowTs);
        if ($email === null || $email === '') {
            return ['status' => 422, 'body' => ['error' => 'invalid_or_expired_token', 'request_id' => $requestId]];
        }

        $this->userStore->resetPassword($email, $newPassword);
        $this->authThrottleStore->clear($email);
        $this->audit('auth.password_reset_completed', $requestId, ['email' => $email]);

        return ['status' => 200, 'body' => ['status' => 'password_reset', 'request_id' => $requestId]];
    }

    /** @param array<string,string> $headers @param array<string,mixed> $env */
    private function me(string $requestId, array $headers, array $env): array
    {
        $auth = $this->requireAuth($requestId, $headers, $env);
        if (isset($auth['response'])) {
            return $auth['response'];
        }
        $user = $auth['user'];
        return ['status' => 200, 'body' => ['id' => $user['id'], 'name' => $user['name'], 'email' => $user['email'], 'role' => $user['role'], 'permissions' => $user['permissions'], 'request_id' => $requestId]];
    }

    /** @param array<string,string> $headers @param array<string,mixed> $env @return array<string,mixed> */
    private function requireAuth(string $requestId, array $headers, array $env): array
    {
        $authHeader = $headers['Authorization'] ?? $headers['authorization'] ?? '';
        $token = str_starts_with($authHeader, 'Bearer ') ? substr($authHeader, 7) : '';
        if ($token === '') {
            return ['response' => ['status' => 401, 'body' => ['error' => 'missing_token', 'request_id' => $requestId]]];
        }
        $secret = (string) ($env['JWT_SECRET'] ?? getenv('JWT_SECRET') ?: 'dev-secret');
        $claims = $this->jwtService->verifyToken($token, $secret);
        if (!$claims || !isset($claims['sub'])) {
            return ['response' => ['status' => 401, 'body' => ['error' => 'invalid_token', 'request_id' => $requestId]]];
        }
        $user = $this->userStore->findByEmail((string) $claims['sub']);
        if (!$user) {
            return ['response' => ['status' => 401, 'body' => ['error' => 'unknown_user', 'request_id' => $requestId]]];
        }
        return ['user' => $user];
    }

    /** @param array<string,string> $headers @param array<string,mixed> $env @return array<string,mixed> */
    private function requirePermission(string $requestId, array $headers, array $env, string $permission): array
    {
        $auth = $this->requireAuth($requestId, $headers, $env);
        if (isset($auth['response'])) {
            return $auth;
        }
        if (!$this->userStore->hasPermission($auth['user'], $permission)) {
            $this->audit('auth.forbidden', $requestId, ['path' => 'permission_scope', 'permission' => $permission]);
            return ['response' => ['status' => 403, 'body' => ['error' => 'forbidden', 'request_id' => $requestId]]];
        }

        return $auth;
    }

    private function resolvePermission(string $method, string $path): ?string
    {
        if ($path === '/admin/ping' && $method === 'GET') {
            return 'admin.ping';
        }


        if ($path === '/families' || preg_match('#^/families/\d+$#', $path) === 1 || $path === '/dependents' || preg_match('#^/dependents/\d+$#', $path) === 1 || $path === '/children' || preg_match('#^/children/\d+$#', $path) === 1) {
            return $method === 'GET' ? 'families.read' : 'families.write';
        }

        if ($path === '/street/people') {
            return $method === 'GET' ? 'street.read' : 'street.write';
        }

        if ($path === '/street/referrals' || preg_match('#^/street/referrals/\d+/status$#', $path) === 1) {
            return 'street.write';
        }

        if ($path === '/deliveries/events' || preg_match('#^/deliveries/events/\d+/(invites|withdrawals)$#', $path) === 1) {
            return $method === 'GET' ? 'delivery.read' : 'delivery.write';
        }

        if ($path === '/equipment' || preg_match('#^/equipment/\d+$#', $path) === 1 || $path === '/equipment/loans' || preg_match('#^/equipment/loans/\d+/return$#', $path) === 1) {
            return $method === 'GET' ? 'equipment.read' : 'equipment.write';
        }

        if ($path === '/reports/summary' || in_array($path, ['/reports/export.csv', '/reports/export.xlsx', '/reports/export.pdf'], true)) {
            return 'reports.read';
        }

        if ($path === '/settings/eligibility') {
            return $method === 'GET' ? 'settings.read' : 'settings.write';
        }

        if ($path === '/eligibility/check') {
            return 'eligibility.check';
        }

        if ($path === '/visits' || preg_match('#^/visits/\d+/complete$#', $path) === 1) {
            return $method === 'GET' ? 'visits.read' : 'visits.write';
        }

        return null;
    }

    /** @param array<string,string> $headers @param array<string,mixed> $env @return array<string,mixed> */
    private function requireWriter(string $requestId, array $headers, array $env): array
    {
        $auth = $this->requireAuth($requestId, $headers, $env);
        if (isset($auth['response'])) {
            return $auth;
        }
        $role = (string) ($auth['user']['role'] ?? '');
        if (!in_array($role, ['admin', 'voluntario', 'pastoral'], true)) {
            $this->audit('auth.forbidden', $requestId, ['path' => 'writer_scope']);
            return ['response' => ['status' => 403, 'body' => ['error' => 'forbidden', 'request_id' => $requestId]]];
        }
        return $auth;
    }

    /** @param array<string, scalar|null> $context */
    private function audit(string $action, string $requestId, array $context): void
    {
        if (!$this->auditLogger) {
            return;
        }
        $this->auditLogger->record($action, array_merge(['request_id' => $requestId], $context));
    }
}
