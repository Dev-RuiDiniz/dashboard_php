<?php

declare(strict_types=1);

namespace App\Auth;

final class UserStore
{
    /** @var array<string, array<string, mixed>> */
    private array $users;

    /** @var array<string, array{email:string,expires_at:int}> */
    private array $resetTokens = [];

    public function __construct()
    {
        $this->users = [
            'admin@local' => [
                'id' => 1,
                'name' => 'Admin',
                'email' => 'admin@local',
                'password_hash' => '$2y$12$H7h85JxZJY6ErgpTFMI0q.rP8fKZr5w4USWl/k5P6SLnoJH5tAYBG',
                'role' => 'admin',
                'permissions' => ['*'],
            ],
            'operador@local' => [
                'id' => 2,
                'name' => 'Operador',
                'email' => 'operador@local',
                'password_hash' => '$2y$12$RQQZ.h8IDSA0xmNJKER5IuEb87ZAY0jYBAd88jNDvT1fbbDO6ture',
                'role' => 'voluntario',
                'permissions' => ['families.read', 'families.write', 'street.read', 'street.write', 'delivery.read', 'delivery.write', 'equipment.read', 'equipment.write', 'reports.read'],
            ],
            'leitura@local' => [
                'id' => 3,
                'name' => 'Leitura',
                'email' => 'leitura@local',
                'password_hash' => '$2y$12$yhJBe0y4WdSRD5uTG59ba.a3Eag5QTdpnSbQiw3c4wl6bMjQFbtQ.',
                'role' => 'viewer',
                'permissions' => ['families.read', 'street.read', 'delivery.read', 'equipment.read', 'reports.read'],
            ],
        ];
    }

    /** @return array<string, array<string, mixed>> */
    public function users(): array
    {
        return $this->users;
    }

    /** @return array<string,mixed>|null */
    public function authenticate(string $email, string $password): ?array
    {
        $user = $this->users[$email] ?? null;
        if (!is_array($user) || !password_verify($password, (string) ($user['password_hash'] ?? ''))) {
            return null;
        }

        return $user;
    }

    /** @return array<string,mixed>|null */
    public function findByEmail(string $email): ?array
    {
        $user = $this->users[$email] ?? null;
        return is_array($user) ? $user : null;
    }

    public function issuePasswordResetToken(string $email, int $expiresAt): ?string
    {
        if (!isset($this->users[$email])) {
            return null;
        }

        $token = bin2hex(random_bytes(24));
        $this->resetTokens[$token] = ['email' => $email, 'expires_at' => $expiresAt];
        return $token;
    }

    public function consumePasswordResetToken(string $token, int $nowTs): ?string
    {
        $state = $this->resetTokens[$token] ?? null;
        if (!is_array($state)) {
            return null;
        }

        unset($this->resetTokens[$token]);
        if (($state['expires_at'] ?? 0) < $nowTs) {
            return null;
        }

        return (string) ($state['email'] ?? '');
    }

    public function resetPassword(string $email, string $newPassword): bool
    {
        if (!isset($this->users[$email])) {
            return false;
        }

        $this->users[$email]['password_hash'] = password_hash($newPassword, PASSWORD_BCRYPT);
        return true;
    }

    /** @param array<string,mixed> $user */
    public function hasPermission(array $user, string $permission): bool
    {
        $permissions = $user['permissions'] ?? [];
        if (!is_array($permissions)) {
            return false;
        }
        if (in_array('*', $permissions, true)) {
            return true;
        }
        return in_array($permission, $permissions, true);
    }
}
