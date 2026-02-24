from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass
from statistics import quantiles
from time import perf_counter

import httpx


@dataclass
class Result:
    status_code: int
    elapsed_ms: float
    ok: bool


async def _single_request(client: httpx.AsyncClient, path: str) -> Result:
    start = perf_counter()
    try:
        response = await client.get(path)
        elapsed_ms = (perf_counter() - start) * 1000
        return Result(
            status_code=response.status_code, elapsed_ms=elapsed_ms, ok=response.status_code < 500
        )
    except httpx.HTTPError:
        elapsed_ms = (perf_counter() - start) * 1000
        return Result(status_code=0, elapsed_ms=elapsed_ms, ok=False)


async def run_load_test(
    base_url: str, path: str, total_requests: int, concurrency: int, timeout: float
) -> list[Result]:
    limits = httpx.Limits(max_connections=concurrency, max_keepalive_connections=concurrency)
    client_timeout = httpx.Timeout(timeout)
    async with httpx.AsyncClient(
        base_url=base_url, timeout=client_timeout, limits=limits
    ) as client:
        semaphore = asyncio.Semaphore(concurrency)

        async def wrapped_request() -> Result:
            async with semaphore:
                return await _single_request(client, path)

        tasks = [asyncio.create_task(wrapped_request()) for _ in range(total_requests)]
        return await asyncio.gather(*tasks)


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    twentieths = quantiles(values, n=100)
    index = max(0, min(99, int(percentile) - 1))
    return twentieths[index]


def main() -> int:
    parser = argparse.ArgumentParser(description="Teste de carga básico para endpoints HTTP.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="URL base da aplicação")
    parser.add_argument("--path", default="/health", help="Path alvo para o teste")
    parser.add_argument("--requests", type=int, default=200, help="Número total de requisições")
    parser.add_argument(
        "--concurrency", type=int, default=20, help="Número de requisições concorrentes"
    )
    parser.add_argument(
        "--timeout", type=float, default=5.0, help="Timeout por requisição em segundos"
    )
    parser.add_argument(
        "--max-error-rate",
        type=float,
        default=0.05,
        help="Taxa máxima de erro aceitável (0.05 = 5%%)",
    )
    parser.add_argument(
        "--max-p95-ms",
        type=float,
        default=500.0,
        help="Latência p95 máxima aceitável em milissegundos",
    )
    args = parser.parse_args()

    if args.requests <= 0 or args.concurrency <= 0:
        raise SystemExit("--requests e --concurrency devem ser maiores que zero")

    results = asyncio.run(
        run_load_test(
            base_url=args.base_url,
            path=args.path,
            total_requests=args.requests,
            concurrency=args.concurrency,
            timeout=args.timeout,
        )
    )

    durations = [result.elapsed_ms for result in results]
    successes = [result for result in results if result.ok]
    errors = len(results) - len(successes)
    error_rate = errors / len(results)
    p95 = _percentile(durations, 95)
    avg = sum(durations) / len(durations)

    print("=== Resultado do teste de carga básico ===")
    print(f"Base URL: {args.base_url}")
    print(f"Path: {args.path}")
    print(f"Total de requisições: {len(results)}")
    print(f"Concorrência: {args.concurrency}")
    print(f"Sucessos (status < 500): {len(successes)}")
    print(f"Erros: {errors} ({error_rate:.2%})")
    print(f"Latência média: {avg:.2f} ms")
    print(f"Latência p95: {p95:.2f} ms")

    ok_error_rate = error_rate <= args.max_error_rate
    ok_latency = p95 <= args.max_p95_ms

    if ok_error_rate and ok_latency:
        print("STATUS: OK")
        return 0

    print("STATUS: FALHA")
    if not ok_error_rate:
        print(f"- Taxa de erro acima do limite: {error_rate:.2%} > {args.max_error_rate:.2%}")
    if not ok_latency:
        print(f"- p95 acima do limite: {p95:.2f} ms > {args.max_p95_ms:.2f} ms")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
