from app.core.security import hash_password, password_needs_rehash, verify_password


def test_new_password_hashes_use_argon2id():
    password_hash = hash_password("correct horse battery staple")

    assert password_hash.startswith("$argon2id$")
    assert verify_password("correct horse battery staple", password_hash)
    assert not verify_password("wrong", password_hash)
    assert not password_needs_rehash(password_hash)
