import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from database.database import Base, get_db
from database.model import User
from auth import get_password_hash


from database.user_add_admin import create_admin_user

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool, 
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)



def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db



@pytest.fixture(scope="function")
def client():
    Base.metadata.create_all(bind=engine)
    # Tworzymy admina w testowej bazie danych: przekazujemy sesję testową
    test_db = TestingSessionLocal()
    try:
        create_admin_user(db=test_db)
    finally:
        test_db.close()
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)


def get_admin_token(client: TestClient):
    response = client.post("/login", data={"username": "admin", "password": "admin123"})
    assert response.status_code == 200, response.json()
    return response.json()["access_token"]

def get_user_token(client: TestClient):
    admin_token = get_admin_token(client)
    headers = {"Authorization": f"Bearer {admin_token}"}
    user_data = {"name": "testuser", "password": "testpassword", "roles": ["USER"]}
    create_response = client.post("/users/", json=user_data, headers=headers)
    assert create_response.status_code == 200, create_response.json()
    
    login_response = client.post("/login", data={"username": "testuser", "password": "testpassword"})
    assert login_response.status_code == 200, login_response.json()
    return login_response.json()["access_token"]



def test_read_root(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}

def test_login_for_access_token(client: TestClient):
    response = client.post("/login", data={"username": "admin", "password": "admin123"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_incorrect_password(client: TestClient):
    response = client.post("/login", data={"username": "admin", "password": "wrongpassword"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password" #Czy powinno być takie dokładne?

def test_read_user_details(client: TestClient):
    token = get_admin_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/user_details", headers=headers)
    assert response.status_code == 200
    assert response.json() == {"username": "admin", "roles": ["ADMIN", "USER"]}

def test_read_user_details_no_token(client: TestClient):
    response = client.get("/user_details")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"



def test_create_user_as_admin(client: TestClient):
    token = get_admin_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post(
        "/users/",
        json={"name": "newuser", "password": "newpassword", "roles": ["USER"]},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "newuser"
    assert data["roles"] == ["USER"]
    assert "id" in data

def test_create_user_as_regular_user(client: TestClient):
    token = get_user_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post(
        "/users/",
        json={"name": "anotheruser", "password": "anotherpassword"},
        headers=headers,
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "The user does not have the required permissions"

def test_get_user_authenticated(client: TestClient):
    token = get_admin_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/users/1", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "admin"
    assert data["id"] == 1

def test_get_user_not_found(client: TestClient):
    token = get_admin_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/users/999", headers=headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"

def test_update_user(client: TestClient):
    token = get_admin_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    update_response = client.put(
        "/users/1",
        json={"name": "superadmin"},
        headers=headers,
    )
    assert update_response.status_code == 200
    data = update_response.json()
    assert data["name"] == "superadmin"
    assert data["id"] == 1

def test_delete_user_as_admin(client: TestClient):
    admin_token = get_admin_token(client)
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    user_to_delete_res = client.post("/users/", json={"name": "todelete", "password": "pw"}, headers=admin_headers)
    user_id = user_to_delete_res.json()["id"]

    delete_response = client.delete(f"/users/{user_id}", headers=admin_headers)
    assert delete_response.status_code == 200
    assert delete_response.json() == {"message": "User deleted successfully"}

    get_response = client.get(f"/users/{user_id}", headers=admin_headers)
    assert get_response.status_code == 404

def test_delete_user_as_regular_user(client: TestClient):
    user_token = get_user_token(client)
    user_headers = {"Authorization": f"Bearer {user_token}"}
    
    response = client.delete("/users/1", headers=user_headers)
    assert response.status_code == 403
    assert response.json()["detail"] == "The user does not have the required permissions"