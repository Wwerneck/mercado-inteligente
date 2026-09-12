from urllib.parse import parse_qs, urlparse

from src.ingestion.oauth import PKCEPair, build_authorization_url, generate_pkce_pair


def test_build_authorization_url_includes_state_and_redirect_uri():
    url = build_authorization_url(
        auth_base_url="https://auth.mercadolivre.com.br",
        client_id="123",
        redirect_uri="http://localhost:8000/auth/meli/callback",
        state="secure-state",
    )

    parsed = urlparse(url)
    params = parse_qs(parsed.query)

    assert parsed.scheme == "https"
    assert parsed.netloc == "auth.mercadolivre.com.br"
    assert parsed.path == "/authorization"
    assert params["response_type"] == ["code"]
    assert params["client_id"] == ["123"]
    assert params["redirect_uri"] == ["http://localhost:8000/auth/meli/callback"]
    assert params["state"] == ["secure-state"]


def test_build_authorization_url_supports_pkce():
    url = build_authorization_url(
        auth_base_url="https://auth.mercadolivre.com.br/",
        client_id="123",
        redirect_uri="https://example.com/callback",
        state="secure-state",
        pkce_pair=PKCEPair(verifier="verifier", challenge="challenge"),
    )

    params = parse_qs(urlparse(url).query)

    assert params["code_challenge"] == ["challenge"]
    assert params["code_challenge_method"] == ["S256"]


def test_generate_pkce_pair_returns_s256_pair():
    pair = generate_pkce_pair()

    assert pair.method == "S256"
    assert len(pair.verifier) >= 43
    assert len(pair.challenge) >= 43
    assert "=" not in pair.challenge
