from bff import versions


def test_model_unknown_when_profile_missing():
    assert versions.model_of("zz-tidak-ada") == (versions.UNKNOWN, versions.UNKNOWN)


def test_soul_hash_unknown_when_missing():
    assert versions.soul_hash("zz-tidak-ada") == versions.UNKNOWN
