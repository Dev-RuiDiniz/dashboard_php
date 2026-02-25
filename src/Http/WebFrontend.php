<?php

declare(strict_types=1);

namespace App\Http;

final class WebFrontend
{
    /**
     * @return array{status:int, headers:array<string,string>, body:string}|null
     */
    public function handle(string $method, string $path, array $routes, array $server): ?array
    {
        if ($method !== 'GET') {
            return null;
        }

        foreach ($routes as $route) {
            if (!is_array($route) || !isset($route['uri'], $route['view'])) {
                continue;
            }
            $params = $this->match((string) $route['uri'], $path);
            if ($params === null) {
                continue;
            }

            $role = (string) ($server['HTTP_X_USER_ROLE'] ?? 'voluntario');
            if (($route['admin_only'] ?? false) === true && $role !== 'admin') {
                return $this->render('errors/forbidden', [
                    'title' => 'Permissão negada',
                    'breadcrumbs' => ['Início', 'Administração'],
                    'route' => $path,
                    'userRole' => $role,
                ], 403);
            }

            return $this->render((string) $route['view'], [
                'title' => (string) ($route['title'] ?? 'Tela'),
                'breadcrumbs' => $route['breadcrumbs'] ?? ['Início'],
                'table' => $route['table'] ?? false,
                'filters' => $route['filters'] ?? [],
                'timeline' => (bool) ($route['timeline'] ?? false),
                'chips' => $route['chips'] ?? [],
                'stub' => (string) ($route['stub'] ?? ''),
                'params' => $params,
                'route' => $path,
            ]);
        }

        return null;
    }

    /** @return array<string,string>|null */
    private function match(string $pattern, string $path): ?array
    {
        $regex = preg_replace('#\{([a-zA-Z0-9_]+)\}#', '(?P<$1>[^/]+)', $pattern);
        if ($regex === null) {
            return null;
        }
        $regex = '#^' . $regex . '$#';
        if (preg_match($regex, $path, $matches) !== 1) {
            return null;
        }

        $params = [];
        foreach ($matches as $key => $value) {
            if (is_string($key)) {
                $params[$key] = (string) $value;
            }
        }

        return $params;
    }

    /**
     * @param array<string,mixed> $data
     * @return array{status:int, headers:array<string,string>, body:string}
     */
    private function render(string $view, array $data, int $status = 200): array
    {
        $viewPath = __DIR__ . '/../../resources/views/' . $view . '.php';
        $layoutPath = __DIR__ . '/../../resources/views/layouts/app.php';

        extract($data, EXTR_SKIP);
        ob_start();
        include $viewPath;
        $content = (string) ob_get_clean();

        ob_start();
        include $layoutPath;
        $body = (string) ob_get_clean();

        return [
            'status' => $status,
            'headers' => ['Content-Type' => 'text/html; charset=utf-8'],
            'body' => $body,
        ];
    }
}
