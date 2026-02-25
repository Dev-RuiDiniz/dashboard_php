<?php

declare(strict_types=1);

namespace App\Auth;

final class UserStore
{
    /**
     * @return array<string, array<string, mixed>>
     */
    public function users(): array
    {
        return [
            'admin@local' => [
                'id' => 1,
                'name' => 'Admin',
                'email' => 'admin@local',
                'password' => 'admin123',
                'role' => 'Admin',
                'permissions' => ['users.manage', 'reports.read', 'families.write'],
            ],
            'operador@local' => [
                'id' => 2,
                'name' => 'Operador',
                'email' => 'operador@local',
                'password' => 'operador123',
                'role' => 'Operador',
                'permissions' => ['reports.read', 'families.write'],
            ],
            'leitura@local' => [
                'id' => 3,
                'name' => 'Leitura',
                'email' => 'leitura@local',
                'password' => 'leitura123',
                'role' => 'Leitura',
                'permissions' => ['reports.read'],
            ],
        ];
    }

    /** @return array<string,mixed>|null */
    public function authenticate(string $email, string $password): ?array
    {
        $user = $this->users()[$email] ?? null;
        if (!is_array($user) || !hash_equals((string) $user['password'], $password)) {
            return null;
        }

        return $user;
    }

    /** @return array<string,mixed>|null */
    public function findByEmail(string $email): ?array
    {
        $user = $this->users()[$email] ?? null;
        return is_array($user) ? $user : null;
    }
}
