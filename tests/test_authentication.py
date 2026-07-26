from werkzeug.security import generate_password_hash, check_password_hash


def test_correct_password():
    password = "password123"
    hashed = generate_password_hash(password)

    assert check_password_hash(hashed, password)


def test_incorrect_password():
    password = "password123"
    hashed = generate_password_hash(password)

    assert not check_password_hash(hashed, "wrongpassword")