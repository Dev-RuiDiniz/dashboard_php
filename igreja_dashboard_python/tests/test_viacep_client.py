from __future__ import annotations

import httpx

from app.services import viacep_client


def test_fetch_address_uses_same_cache_key_for_normalized_cep(monkeypatch):
    viacep_client._CEP_CACHE.clear()
    calls = {"count": 0}

    def fake_get(url: str, timeout: float):
        calls["count"] += 1

        class Response:
            def raise_for_status(self):
                return None

            def json(self):
                return {
                    "cep": "01001-000",
                    "logradouro": "Praça da Sé",
                    "bairro": "Sé",
                    "localidade": "São Paulo",
                    "uf": "sp",
                    "complemento": "lado ímpar",
                }

        return Response()

    monkeypatch.setattr(httpx, "get", fake_get)

    first = viacep_client.fetch_address_by_cep("01001-000")
    second = viacep_client.fetch_address_by_cep("01001000")

    assert calls["count"] == 1
    assert first.cep == "01001000"
    assert second.cep == "01001000"
