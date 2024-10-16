import pytest
from fastapi.testclient import TestClient
from faker import Faker
import base64
from http import HTTPStatus
from pydantic import SecretStr
from lecture_4.demo_service.api.contracts import UserResponse, RegisterUserRequest
from lecture_4.demo_service.api.main import create_app
from lecture_4.demo_service.core.users import UserInfo, UserRole


app = create_app()
faker = Faker()


@pytest.fixture()
def client():
    with TestClient(app) as client:
        yield client


@pytest.fixture()
def birthdate():
    return faker.date_time().isoformat()


@pytest.fixture()
def password():
    return "strongpassword123"


@pytest.fixture()
def admin_credentials():
    return base64.b64encode("admin:superSecretAdminPassword123".encode()).decode()


@pytest.fixture()
def user_info(birthdate, password):
    return UserInfo(
        username="user_woopsen",
        name="name_poopsen",
        birthdate=birthdate,
        role=UserRole.USER,
        password=SecretStr(password)
    )


@pytest.fixture()
def user(client, password, birthdate, user_info):
    data = {
        'username': user_info.username,
        'name': user_info.name,
        'birthdate': birthdate,
        'password': password,
    }
    resp = client.post('/user-register', json=data)
    assert resp.status_code == HTTPStatus.OK
    json = resp.json()
    return UserResponse(uid=json['uid'], username=data['username'], name=data['name'], birthdate=data['birthdate'], role=json['role'])


@pytest.fixture()
def register_user_request(user_info, password):
    return RegisterUserRequest(
        username=user_info.username,
        name=user_info.name,
        birthdate=user_info.birthdate,
        password=password
    )
