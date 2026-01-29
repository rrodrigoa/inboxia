from app.utils.subjects import normalize_subject


def test_normalize_subject():
    assert normalize_subject("Re: Hello") == "hello"
    assert normalize_subject("Fwd: RE: Update") == "update"
    assert normalize_subject("") == "(no subject)"
