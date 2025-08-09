import requests
import pytest
import config
token = config.STATIC_CRON_TOKEN

def test_get_about():
    response = requests.get(config.BASE_URL + '/about')
    assert response.status_code == 200

def test_get_about_user():
    response = requests.get(config.BASE_URL + '/about/user')
    assert response.status_code == 200

def test_get_about_cron_cli_token():
    print(token,"token for me ")
    response = requests.get(config.BASE_URL + f'/cron/{token}', headers=config.HEADERS)
    assert response.status_code == 200