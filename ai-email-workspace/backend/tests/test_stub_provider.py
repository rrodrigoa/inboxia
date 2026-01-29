from app.providers.stub import LocalStubProvider


def test_stub_provider_deterministic():
    provider = LocalStubProvider()
    vec1 = provider.embed(["hello"])[0]
    vec2 = provider.embed(["hello"])[0]
    assert vec1 == vec2
    assert len(vec1) == 1536
    answer = provider.chat("question")
    assert "Stub response" in answer
