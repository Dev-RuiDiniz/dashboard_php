<?php

declare(strict_types=1);

namespace App\Domain;

final class EquipmentStore
{
    private string $storagePath;

    public function __construct(?string $storagePath = null)
    {
        $this->storagePath = $storagePath ?? __DIR__ . '/../../data/equipment_store.json';
        $dir = dirname($this->storagePath);
        if (!is_dir($dir)) {
            mkdir($dir, 0777, true);
        }
    }

    /** @return array<string,mixed> */
    private function load(): array
    {
        if (!file_exists($this->storagePath)) {
            return ['equipments'=>[], 'loans'=>[], 'equipmentSeq'=>1, 'loanSeq'=>1];
        }
        $d = json_decode(file_get_contents($this->storagePath) ?: '{}', true);
        if (!is_array($d)) {
            return ['equipments'=>[], 'loans'=>[], 'equipmentSeq'=>1, 'loanSeq'=>1];
        }
        $d['equipments']=$d['equipments']??[]; $d['loans']=$d['loans']??[];
        $d['equipmentSeq']=(int)($d['equipmentSeq']??1); $d['loanSeq']=(int)($d['loanSeq']??1);
        return $d;
    }

    /** @param array<string,mixed> $d */
    private function save(array $d): void
    {
        file_put_contents($this->storagePath, json_encode($d, JSON_UNESCAPED_UNICODE|JSON_PRETTY_PRINT));
    }

    /** @return array<int,array<string,mixed>> */
    public function listEquipments(): array { return array_values($this->load()['equipments']); }

    /** @return array<string,mixed> */
    public function createEquipment(string $type, string $condition, string $notes): array
    {
        $d=$this->load(); $id=(int)$d['equipmentSeq']; $d['equipmentSeq']=$id+1;
        $code='EQ-'.str_pad((string)$id,4,'0',STR_PAD_LEFT);
        $e=['id'=>$id,'code'=>$code,'type'=>$type,'status'=>'disponivel','condition'=>$condition,'notes'=>$notes];
        $d['equipments'][(string)$id]=$e; $this->save($d); return $e;
    }

    /** @return array<string,mixed>|null */
    public function updateEquipment(int $id, string $status, string $condition, string $notes): ?array
    {
        $d=$this->load(); if (!isset($d['equipments'][(string)$id])) return null;
        if (!in_array($status,['disponivel','emprestado','manutencao'],true)) return ['error'=>'invalid_status'];
        $d['equipments'][(string)$id]['status']=$status;
        $d['equipments'][(string)$id]['condition']=$condition;
        $d['equipments'][(string)$id]['notes']=$notes;
        $this->save($d); return $d['equipments'][(string)$id];
    }

    /** @return array<string,mixed>|null */
    public function createLoan(int $equipmentId, int $familyId, string $dueDate): ?array
    {
        $d=$this->load();
        if (!isset($d['equipments'][(string)$equipmentId])) return null;
        if ((string)$d['equipments'][(string)$equipmentId]['status'] !== 'disponivel') return ['error'=>'equipment_unavailable'];
        $id=(int)$d['loanSeq']; $d['loanSeq']=$id+1;
        $loan=['id'=>$id,'equipment_id'=>$equipmentId,'family_id'=>$familyId,'due_date'=>$dueDate,'status'=>'aberto'];
        $d['loans'][(string)$id]=$loan;
        $d['equipments'][(string)$equipmentId]['status']='emprestado';
        $this->save($d);
        return $loan;
    }

    /** @return array<string,mixed>|null */
    public function returnLoan(int $loanId, string $condition, string $notes): ?array
    {
        $d=$this->load();
        if (!isset($d['loans'][(string)$loanId])) return null;
        if ((string)$d['loans'][(string)$loanId]['status'] !== 'aberto') return ['error'=>'loan_closed'];
        $equipId=(int)$d['loans'][(string)$loanId]['equipment_id'];
        $d['loans'][(string)$loanId]['status']='devolvido';
        $d['loans'][(string)$loanId]['return_condition']=$condition;
        $d['loans'][(string)$loanId]['return_notes']=$notes;
        if (isset($d['equipments'][(string)$equipId])) {
            $d['equipments'][(string)$equipId]['status']='disponivel';
            $d['equipments'][(string)$equipId]['condition']=$condition;
            $d['equipments'][(string)$equipId]['notes']=$notes;
        }
        $this->save($d);
        return $d['loans'][(string)$loanId];
    }

    /** @return array<int,array<string,mixed>> */
    public function listLoans(): array { return array_values($this->load()['loans']); }

    public function reset(): void { if (file_exists($this->storagePath)) unlink($this->storagePath); }
}
