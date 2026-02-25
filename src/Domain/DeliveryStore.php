<?php

declare(strict_types=1);

namespace App\Domain;

final class DeliveryStore
{
    private string $storagePath;

    public function __construct(?string $storagePath = null)
    {
        $this->storagePath = $storagePath ?? __DIR__ . '/../../data/delivery_store.json';
        $dir = dirname($this->storagePath);
        if (!is_dir($dir)) {
            mkdir($dir, 0777, true);
        }
    }

    /** @return array<string,mixed> */
    private function load(): array
    {
        if (!file_exists($this->storagePath)) {
            return ['events'=>[], 'invites'=>[], 'withdrawals'=>[], 'eventSeq'=>1, 'inviteSeq'=>1, 'withdrawSeq'=>1];
        }
        $d = json_decode(file_get_contents($this->storagePath) ?: '{}', true);
        if (!is_array($d)) {
            return ['events'=>[], 'invites'=>[], 'withdrawals'=>[], 'eventSeq'=>1, 'inviteSeq'=>1, 'withdrawSeq'=>1];
        }
        $d['events']=$d['events']??[]; $d['invites']=$d['invites']??[]; $d['withdrawals']=$d['withdrawals']??[];
        $d['eventSeq']=(int)($d['eventSeq']??1); $d['inviteSeq']=(int)($d['inviteSeq']??1); $d['withdrawSeq']=(int)($d['withdrawSeq']??1);
        return $d;
    }

    /** @param array<string,mixed> $d */
    private function save(array $d): void
    {
        file_put_contents($this->storagePath, json_encode($d, JSON_UNESCAPED_UNICODE|JSON_PRETTY_PRINT));
    }

    /** @return array<int,array<string,mixed>> */
    public function listEvents(): array { return array_values($this->load()['events']); }

    /** @return array<string,mixed> */
    public function createEvent(string $name, string $date): array
    {
        $d=$this->load(); $id=(int)$d['eventSeq']; $d['eventSeq']=$id+1;
        $event=['id'=>$id,'name'=>$name,'event_date'=>$date,'status'=>'aberto'];
        $d['events'][(string)$id]=$event; $this->save($d); return $event;
    }

    /** @return array<string,mixed>|null */
    public function inviteFamily(int $eventId, int $familyId): ?array
    {
        $d=$this->load(); if (!isset($d['events'][(string)$eventId])) return null;
        foreach ($d['invites'] as $inv) {
            if ((int)$inv['event_id']===$eventId && (int)$inv['family_id']===$familyId) return $inv;
        }
        $id=(int)$d['inviteSeq']; $d['inviteSeq']=$id+1;
        $code=strtoupper(substr(hash('sha256', $eventId.'-'.$familyId.'-'.$id),0,6));
        $invite=['id'=>$id,'event_id'=>$eventId,'family_id'=>$familyId,'withdrawal_code'=>$code,'status'=>'presente'];
        $d['invites'][(string)$id]=$invite; $this->save($d); return $invite;
    }

    public function hasFamilyWithdrawalInMonth(int $familyId, string $eventDate): bool
    {
        $month=substr($eventDate,0,7);
        $d=$this->load();
        foreach ($d['withdrawals'] as $w) {
            if ((int)$w['family_id']!==$familyId) continue;
            $eid=(string)$w['event_id'];
            $date=(string)($d['events'][$eid]['event_date'] ?? '');
            if (substr($date,0,7)===$month) return true;
        }
        return false;
    }

    /** @return array<string,mixed>|null */
    public function registerWithdrawal(int $eventId, int $familyId, bool $signatureAccepted, string $signatureName): ?array
    {
        $d=$this->load();
        if (!isset($d['events'][(string)$eventId])) return null;
        if ($this->hasFamilyWithdrawalInMonth($familyId, (string)$d['events'][(string)$eventId]['event_date'])) return ['error'=>'duplicate_month'];
        if (!$signatureAccepted || trim($signatureName)==='') return ['error'=>'signature_required'];
        $id=(int)$d['withdrawSeq']; $d['withdrawSeq']=$id+1;
        $w=['id'=>$id,'event_id'=>$eventId,'family_id'=>$familyId,'signature_accepted'=>$signatureAccepted,'signature_name'=>$signatureName,'status'=>'retirou'];
        $d['withdrawals'][(string)$id]=$w; $this->save($d); return $w;
    }

    public function reset(): void { if (file_exists($this->storagePath)) unlink($this->storagePath); }
}
