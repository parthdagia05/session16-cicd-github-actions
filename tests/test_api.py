import pytest

from app.main import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    return app.test_client()


def test_index(client):
    res = client.get("/")
    assert res.status_code == 200
    assert "add" in res.get_json()["operations"]


def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.get_json()["status"] == "ok"


def test_calc_add(client):
    res = client.get("/calc/add?a=10&b=5")
    assert res.status_code == 200
    assert res.get_json()["result"] == 15


def test_calc_divide_by_zero(client):
    res = client.get("/calc/divide?a=1&b=0")
    assert res.status_code == 400


def test_calc_bad_input(client):
    res = client.get("/calc/add?a=x&b=5")
    assert res.status_code == 400


def test_calc_unknown_op(client):
    res = client.get("/calc/power?a=2&b=3")
    assert res.status_code == 404
