"""Typed results returned by :class:`veritify.VeritifyClient`.

These mirror the response contract of the Veritify API exactly (field names
and meaning). ``from_dict`` silently ignores any extra keys the API might add
in the future, so an older SDK version keeps working against a newer server.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Any


def _from_dict(cls: type, data: dict[str, Any]):
    known = {f.name for f in fields(cls)}
    return cls(**{k: v for k, v in data.items() if k in known})


@dataclass(frozen=True)
class MineResult:
    """Result of processing a single file (no `question` passed to `mine()`)."""

    mode: str
    delta_s: float
    e0_normalized: float
    regime: float
    eigenvalues: list[float]
    is_novel: bool
    energy_concentration: str
    regime_name: str
    discontinuity: bool
    original_format: str
    receipt_hash: str
    lambda_snapshot: dict[str, float]
    processing_ms: int
    n_chunks: int
    compression_ratio: float
    spectral_flatness: float = 0.0
    noise_suspect: bool = False
    teacher_address: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MineResult":
        return _from_dict(cls, data)


@dataclass(frozen=True)
class MineResultDual:
    """Result of comparing a file against a `question` (dual pipeline)."""

    mode: str
    data_e0: float
    data_regime: str
    data_energy_concentration: str
    query_e0: float
    query_regime: str
    geometric_overlap: float
    spectral_resonance: float
    regime_alignment: float
    verdict: str
    is_novel: bool
    delta_s: float
    original_format: str
    receipt_hash: str
    lambda_snapshot: dict[str, float]
    processing_ms: int
    n_chunks: int
    spectral_flatness: float = 0.0
    noise_suspect: bool = False
    teacher_address: str | None = None
    cross_modal: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MineResultDual":
        return _from_dict(cls, data)


@dataclass(frozen=True)
class VerifyResult:
    """Public verification of a receipt hash.

    ``known=False`` means the hash was never seen by this server. When
    ``known=True`` but the receipt was migrated from an older checkpoint,
    the detail fields may be ``None`` ("existence confirmed, details
    unavailable") rather than absent.
    """

    receipt_hash: str
    known: bool
    mined_at: float | None = None
    delta_s: float | None = None
    e0_normalized: float | None = None
    regime: float | None = None
    is_novel: bool | None = None
    original_format: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VerifyResult":
        return _from_dict(cls, data)


@dataclass(frozen=True)
class HealthStatus:
    status: str
    device: str
    chunk_size: int
    uptime_s: float

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HealthStatus":
        return _from_dict(cls, data)


@dataclass(frozen=True)
class Stats:
    total_processed: int
    novel_count: int
    novelty_rate: float
    dual_query_count: int
    lambda_current: dict[str, float]
    g_base_dimension: int
    g_base_nonzero: int

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Stats":
        return _from_dict(cls, data)


@dataclass(frozen=True)
class SignupResult:
    """Resultado de `VeritifyClient.signup()`.

    ``api_key`` só existe UMA VEZ, neste retorno — a Veritify não guarda a
    chave em texto puro e não consegue mostrá-la de novo depois.
    """

    api_key: str
    plan: str
    message: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SignupResult":
        return _from_dict(cls, data)


@dataclass(frozen=True)
class UsageResult:
    """Resultado de `VeritifyClient.usage()` — histórico de uso da própria
    chave de API. Uma chave nunca usada tem `total_calls=0` e os dois
    timestamps `None` — não é um erro, é o estado normal de uma chave nova.
    """

    total_calls: int
    first_used_at: float | None = None
    last_used_at: float | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UsageResult":
        return _from_dict(cls, data)
