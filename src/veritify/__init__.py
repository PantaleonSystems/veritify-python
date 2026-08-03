"""Veritify — official Python SDK.

    from veritify import VeritifyClient

    client = VeritifyClient(base_url="http://localhost:8000")
    result = client.mine("recording.wav")
    print(result.is_novel, result.delta_s, result.receipt_hash)

    verification = client.verify(result.receipt_hash)
    print(verification.known)
"""

from ._version import __version__
from .client import VeritifyClient
from .exceptions import VeritifyAPIError, VeritifyConnectionError, VeritifyError
from .models import HealthStatus, MineResult, MineResultDual, Stats, VerifyResult

__all__ = [
    "VeritifyClient",
    "VeritifyError",
    "VeritifyAPIError",
    "VeritifyConnectionError",
    "MineResult",
    "MineResultDual",
    "VerifyResult",
    "HealthStatus",
    "Stats",
    "__version__",
]
