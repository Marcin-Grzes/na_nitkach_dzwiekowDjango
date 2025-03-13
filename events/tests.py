import pytest


def test_status():
    assert True


@pytest.mark.django_db
def test_status():
    assert True
