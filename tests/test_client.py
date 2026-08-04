"""Tests for VeritifyClient — HTTP is mocked (responses), no real server needed."""

from __future__ import annotations

import pytest
import responses

from veritify import VeritifyClient
from veritify.exceptions import VeritifyAPIError, VeritifyConnectionError

BASE_URL = "http://localhost:8000"


@pytest.fixture
def client():
    return VeritifyClient(base_url=BASE_URL, api_key="test-key")


_MINE_SINGLE_PAYLOAD = {
    "mode": "single",
    "delta_s": 0.0042,
    "e0_normalized": 0.87,
    "regime": 0.91,
    "eigenvalues": [1.0] * 8,
    "is_novel": True,
    "energy_concentration": "ALTA",
    "regime_name": "QUÂNTICO",
    "discontinuity": False,
    "original_format": "audio/wav",
    "receipt_hash": "a" * 64,
    "lambda_snapshot": {"routing": 1.0},
    "processing_ms": 120,
    "n_chunks": 4,
    "compression_ratio": 277.0,
}

_MINE_DUAL_PAYLOAD = {
    "mode": "dual",
    "data_e0": 0.5,
    "data_regime": "QUÂNTICO",
    "data_energy_concentration": "ALTA",
    "query_e0": 0.4,
    "query_regime": "QUÂNTICO",
    "geometric_overlap": 0.8,
    "spectral_resonance": 0.7,
    "regime_alignment": 0.9,
    "verdict": "PADRÃO DETECTADO — SEVERIDADE ALTA",
    "is_novel": True,
    "delta_s": 0.01,
    "original_format": "text/plain",
    "receipt_hash": "b" * 64,
    "lambda_snapshot": {},
    "processing_ms": 90,
    "n_chunks": 2,
}


class TestMine:
    @responses.activate
    def test_single_mode_when_no_question(self, client, tmp_path):
        responses.add(
            responses.POST, f"{BASE_URL}/api/v1/mine", json=_MINE_SINGLE_PAYLOAD, status=200
        )
        f = tmp_path / "sample.wav"
        f.write_bytes(b"fake-audio-bytes")

        result = client.mine(f)

        assert result.mode == "single"
        assert result.delta_s == 0.0042
        assert result.is_novel is True
        assert result.receipt_hash == "a" * 64
        assert len(result.eigenvalues) == 8

    @responses.activate
    def test_dual_mode_when_question_provided(self, client, tmp_path):
        responses.add(
            responses.POST, f"{BASE_URL}/api/v1/mine", json=_MINE_DUAL_PAYLOAD, status=200
        )
        f = tmp_path / "doc.txt"
        f.write_text("hello")

        result = client.mine(f, question="is this anomalous?")

        assert result.mode == "dual"
        assert result.verdict == "PADRÃO DETECTADO — SEVERIDADE ALTA"

    @responses.activate
    def test_sends_question_as_form_field(self, client, tmp_path):
        responses.add(
            responses.POST, f"{BASE_URL}/api/v1/mine", json=_MINE_DUAL_PAYLOAD, status=200
        )
        f = tmp_path / "doc.txt"
        f.write_text("hello")

        client.mine(f, question="is this anomalous?")

        sent_body = responses.calls[0].request.body.decode("utf-8", errors="ignore")
        assert "is this anomalous?" in sent_body

    @responses.activate
    def test_raises_veritify_api_error_on_4xx(self, client, tmp_path):
        responses.add(
            responses.POST,
            f"{BASE_URL}/api/v1/mine",
            json={"detail": "Arquivo vazio"},
            status=422,
        )
        f = tmp_path / "empty.txt"
        f.write_text("")

        with pytest.raises(VeritifyAPIError) as exc_info:
            client.mine(f)
        assert exc_info.value.status_code == 422
        assert "Arquivo vazio" in exc_info.value.detail

    @responses.activate
    def test_ignores_unknown_fields_from_future_api_versions(self, client, tmp_path):
        payload = dict(_MINE_SINGLE_PAYLOAD, some_future_field="unexpected")
        responses.add(responses.POST, f"{BASE_URL}/api/v1/mine", json=payload, status=200)
        f = tmp_path / "sample.wav"
        f.write_bytes(b"x")

        result = client.mine(f)  # must not raise
        assert result.delta_s == 0.0042


class TestVerify:
    @responses.activate
    def test_known_receipt(self, client):
        h = "c" * 64
        responses.add(
            responses.GET,
            f"{BASE_URL}/api/v1/verify/{h}",
            json={
                "receipt_hash": h,
                "known": True,
                "mined_at": 1752500000.0,
                "delta_s": 0.0042,
                "e0_normalized": 0.87,
                "regime": 0.91,
                "is_novel": True,
                "original_format": "text/plain",
            },
            status=200,
        )
        result = client.verify(h)
        assert result.known is True
        assert result.receipt_hash == h
        assert result.mined_at == 1752500000.0

    @responses.activate
    def test_unknown_receipt_returns_known_false_not_an_error(self, client):
        h = "d" * 64
        responses.add(
            responses.GET,
            f"{BASE_URL}/api/v1/verify/{h}",
            json={
                "receipt_hash": h,
                "known": False,
                "mined_at": None,
                "delta_s": None,
                "e0_normalized": None,
                "regime": None,
                "is_novel": None,
                "original_format": None,
            },
            status=200,
        )
        result = client.verify(h)
        assert result.known is False
        assert result.delta_s is None

    @responses.activate
    def test_malformed_hash_raises_api_error(self, client):
        responses.add(
            responses.GET,
            f"{BASE_URL}/api/v1/verify/not-a-hash",
            json={"detail": "receipt_hash deve ser um SHA-256"},
            status=422,
        )
        with pytest.raises(VeritifyAPIError) as exc_info:
            client.verify("not-a-hash")
        assert exc_info.value.status_code == 422


class TestHealthAndStats:
    @responses.activate
    def test_health(self, client):
        responses.add(
            responses.GET,
            f"{BASE_URL}/health",
            json={"status": "ok", "device": "cpu", "chunk_size": 256, "uptime_s": 12.3},
            status=200,
        )
        health = client.health()
        assert health.status == "ok"
        assert health.chunk_size == 256

    @responses.activate
    def test_stats(self, client):
        responses.add(
            responses.GET,
            f"{BASE_URL}/stats",
            json={
                "total_processed": 10,
                "novel_count": 4,
                "novelty_rate": 0.4,
                "dual_query_count": 2,
                "lambda_current": {"routing": 1.0},
                "g_base_dimension": 256,
                "g_base_nonzero": 100,
            },
            status=200,
        )
        stats = client.stats()
        assert stats.total_processed == 10
        assert stats.novelty_rate == 0.4

    @responses.activate
    def test_health_and_stats_hit_root_not_api_v1(self, client):
        """Real quirk of the API: /health and /stats have no /api/v1 prefix."""
        responses.add(
            responses.GET,
            f"{BASE_URL}/health",
            json={"status": "ok", "device": "cpu", "chunk_size": 256, "uptime_s": 1.0},
            status=200,
        )
        client.health()
        assert responses.calls[0].request.url == f"{BASE_URL}/health"


class TestClientConfig:
    def test_requires_base_url_one_way_or_the_other(self, monkeypatch):
        monkeypatch.delenv("VERITIFY_BASE_URL", raising=False)
        with pytest.raises(ValueError):
            VeritifyClient()

    def test_reads_base_url_from_environment(self, monkeypatch):
        monkeypatch.setenv("VERITIFY_BASE_URL", BASE_URL)
        client = VeritifyClient()
        assert client.base_url == BASE_URL

    def test_explicit_base_url_wins_over_env(self, monkeypatch):
        monkeypatch.setenv("VERITIFY_BASE_URL", "http://env-value:9999")
        client = VeritifyClient(base_url=BASE_URL)
        assert client.base_url == BASE_URL

    def test_trailing_slash_in_base_url_is_stripped(self):
        client = VeritifyClient(base_url=f"{BASE_URL}/")
        assert client.base_url == BASE_URL

    @responses.activate
    def test_api_key_sent_as_bearer_token(self, tmp_path):
        client = VeritifyClient(base_url=BASE_URL, api_key="secret-123")
        responses.add(
            responses.GET,
            f"{BASE_URL}/health",
            json={"status": "ok", "device": "cpu", "chunk_size": 256, "uptime_s": 1.0},
            status=200,
        )
        client.health()
        assert responses.calls[0].request.headers["Authorization"] == "Bearer secret-123"

    def test_reads_api_key_from_environment(self, monkeypatch):
        monkeypatch.setenv("VERITIFY_API_KEY", "from-env-123")
        client = VeritifyClient(base_url=BASE_URL)
        assert client.api_key == "from-env-123"

    def test_explicit_api_key_wins_over_env(self, monkeypatch):
        monkeypatch.setenv("VERITIFY_API_KEY", "from-env-123")
        client = VeritifyClient(base_url=BASE_URL, api_key="explicit-456")
        assert client.api_key == "explicit-456"

    def test_connection_error_is_wrapped(self):
        client = VeritifyClient(base_url="http://localhost:1")  # nothing listens here
        with pytest.raises(VeritifyConnectionError):
            client.health()

    def test_context_manager_closes_session(self):
        with VeritifyClient(base_url=BASE_URL) as client:
            assert client.base_url == BASE_URL


class TestSignup:
    """signup() — o único método pensado para funcionar SEM api_key prévia."""

    @responses.activate
    def test_signup_success(self):
        client = VeritifyClient(base_url=BASE_URL)
        responses.add(
            responses.POST,
            f"{BASE_URL}/api/v1/signup",
            json={
                "api_key": "vrfy_live_abc123",
                "plan": "free",
                "message": "Guarde esta chave agora.",
            },
            status=201,
        )
        result = client.signup("dev@example.com")
        assert result.api_key == "vrfy_live_abc123"
        assert result.plan == "free"
        assert result.message == "Guarde esta chave agora."

    @responses.activate
    def test_signup_sends_email_in_body(self):
        client = VeritifyClient(base_url=BASE_URL)
        responses.add(
            responses.POST,
            f"{BASE_URL}/api/v1/signup",
            json={"api_key": "vrfy_live_x", "plan": "free", "message": "m"},
            status=201,
        )
        client.signup("dev@example.com")
        sent_body = responses.calls[0].request.body
        assert b"dev@example.com" in sent_body

    @responses.activate
    def test_signup_conflict_raises_api_error(self):
        client = VeritifyClient(base_url=BASE_URL)
        responses.add(
            responses.POST,
            f"{BASE_URL}/api/v1/signup",
            json={"detail": "dev@example.com ja possui uma chave ativa"},
            status=409,
        )
        with pytest.raises(VeritifyAPIError) as exc_info:
            client.signup("dev@example.com")
        assert exc_info.value.status_code == 409

    @responses.activate
    def test_signup_invalid_email_raises_api_error(self):
        client = VeritifyClient(base_url=BASE_URL)
        responses.add(
            responses.POST,
            f"{BASE_URL}/api/v1/signup",
            json={"detail": "email invalido"},
            status=422,
        )
        with pytest.raises(VeritifyAPIError) as exc_info:
            client.signup("not-an-email")
        assert exc_info.value.status_code == 422

    @responses.activate
    def test_signup_rate_limited_raises_api_error(self):
        client = VeritifyClient(base_url=BASE_URL)
        responses.add(
            responses.POST,
            f"{BASE_URL}/api/v1/signup",
            json={"detail": "Muitos cadastros deste IP"},
            status=429,
            headers={"Retry-After": "30"},
        )
        with pytest.raises(VeritifyAPIError) as exc_info:
            client.signup("dev@example.com")
        assert exc_info.value.status_code == 429

    @responses.activate
    def test_signup_works_without_api_key_set(self):
        """signup é o único endpoint pensado pra funcionar sem chave prévia."""
        client = VeritifyClient(base_url=BASE_URL)  # sem api_key=
        assert client.api_key is None
        responses.add(
            responses.POST,
            f"{BASE_URL}/api/v1/signup",
            json={"api_key": "vrfy_live_y", "plan": "free", "message": "m"},
            status=201,
        )
        result = client.signup("noauth@example.com")
        assert result.api_key == "vrfy_live_y"
        # confirma que a chamada não mandou Authorization (nada configurado)
        assert "Authorization" not in responses.calls[0].request.headers


class TestUsage:
    """usage() — histórico de uso da própria chave (GET /api/v1/usage)."""

    @responses.activate
    def test_usage_success(self):
        client = VeritifyClient(base_url=BASE_URL, api_key="vrfy_live_abc")
        responses.add(
            responses.GET,
            f"{BASE_URL}/api/v1/usage",
            json={
                "total_calls": 3,
                "first_used_at": 100.0,
                "last_used_at": 300.0,
            },
            status=200,
        )
        result = client.usage()
        assert result.total_calls == 3
        assert result.first_used_at == 100.0
        assert result.last_used_at == 300.0

    @responses.activate
    def test_usage_never_used_key(self):
        client = VeritifyClient(base_url=BASE_URL, api_key="vrfy_live_abc")
        responses.add(
            responses.GET,
            f"{BASE_URL}/api/v1/usage",
            json={"total_calls": 0, "first_used_at": None, "last_used_at": None},
            status=200,
        )
        result = client.usage()
        assert result.total_calls == 0
        assert result.first_used_at is None
        assert result.last_used_at is None

    @responses.activate
    def test_usage_sends_authorization_header(self):
        client = VeritifyClient(base_url=BASE_URL, api_key="vrfy_live_abc")
        responses.add(
            responses.GET,
            f"{BASE_URL}/api/v1/usage",
            json={"total_calls": 0, "first_used_at": None, "last_used_at": None},
            status=200,
        )
        client.usage()
        assert responses.calls[0].request.headers["Authorization"] == "Bearer vrfy_live_abc"

    @responses.activate
    def test_usage_without_api_key_raises_api_error(self):
        client = VeritifyClient(base_url=BASE_URL)  # sem api_key=
        responses.add(
            responses.GET,
            f"{BASE_URL}/api/v1/usage",
            json={"detail": "Authorization ausente."},
            status=401,
        )
        with pytest.raises(VeritifyAPIError) as exc_info:
            client.usage()
        assert exc_info.value.status_code == 401

    @responses.activate
    def test_usage_invalid_key_raises_api_error(self):
        client = VeritifyClient(base_url=BASE_URL, api_key="vrfy_live_bad")
        responses.add(
            responses.GET,
            f"{BASE_URL}/api/v1/usage",
            json={"detail": "Chave de API invalida ou revogada."},
            status=401,
        )
        with pytest.raises(VeritifyAPIError) as exc_info:
            client.usage()
        assert exc_info.value.status_code == 401
