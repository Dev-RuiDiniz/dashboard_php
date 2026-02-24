from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import re

import httpx


class ViaCEPError(Exception):
    """Erro esperado na integração com o ViaCEP."""


class ViaCEPInvalidCEPError(ViaCEPError):
    """CEP informado em formato inválido."""


class ViaCEPNotFoundError(ViaCEPError):
    """CEP não encontrado na base do ViaCEP."""


class ViaCEPUnavailableError(ViaCEPError):
    """Falha de disponibilidade no serviço externo ViaCEP."""


@dataclass(slots=True)
class ViaCEPAddress:
    cep: str
    street: str
    neighborhood: str
    city: str
    state: str
    complement: str


_CEP_REGEX = re.compile(r"\D")
_CACHE_TTL = timedelta(hours=24)
_CEP_CACHE: dict[str, tuple[ViaCEPAddress, datetime]] = {}


def normalize_cep(raw_cep: str) -> str:
    cep = _CEP_REGEX.sub("", raw_cep or "")
    if len(cep) != 8:
        raise ViaCEPInvalidCEPError("CEP deve conter 8 dígitos.")
    return cep


def fetch_address_by_cep(raw_cep: str, timeout_seconds: float = 3.0) -> ViaCEPAddress:
    cep = normalize_cep(raw_cep)
    cached = _CEP_CACHE.get(cep)
    now = datetime.now(timezone.utc)
    if cached and cached[1] > now:
        return cached[0]

    url = f"https://viacep.com.br/ws/{cep}/json/"
    try:
        response = httpx.get(url, timeout=timeout_seconds)
        response.raise_for_status()
        payload = response.json()
    except httpx.TimeoutException as exc:
        raise ViaCEPUnavailableError("Consulta de CEP indisponível no momento (timeout).") from exc
    except httpx.HTTPError as exc:
        raise ViaCEPUnavailableError("Falha ao consultar o serviço de CEP.") from exc

    if payload.get("erro") is True:
        raise ViaCEPNotFoundError("CEP não encontrado.")

    result = ViaCEPAddress(
        cep=normalize_cep(payload.get("cep", cep)),
        street=(payload.get("logradouro") or "").strip(),
        neighborhood=(payload.get("bairro") or "").strip(),
        city=(payload.get("localidade") or "").strip(),
        state=(payload.get("uf") or "").strip().upper(),
        complement=(payload.get("complemento") or "").strip(),
    )
    _CEP_CACHE[cep] = (result, now + _CACHE_TTL)
    return result
