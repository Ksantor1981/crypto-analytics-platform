import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_register_new_user_success(async_client: AsyncClient):
    """Тест успешной регистрации нового пользователя."""
    user_data = {
        "email": "test@example.com",
        "password": "strongpassword123",
        "confirm_password": "strongpassword123",
        "full_name": "Test User"
    }
    response = await async_client.post("/api/v1/users/register", json=user_data)
    print(f"Response status: {response.status_code}")
    print(f"Response content: {response.text}")
    assert response.status_code == 201, f"Expected 201, got {response.status_code}. Response: {response.text}"
    response_data = response.json()
    assert response_data["email"] == user_data["email"]
    assert "id" in response_data
    assert "access_token" not in response_data  # Токен не должен возвращаться при регистрации


async def test_register_existing_user_fails(async_client: AsyncClient):
    """Тест ошибки при регистрации пользователя с существующим email."""
    user_data = {
        "email": "test2@example.com",
        "password": "strongpassword123",
        "confirm_password": "strongpassword123",
        "full_name": "Test User"
    }
    
    # Первая регистрация должна быть успешной
    response = await async_client.post("/api/v1/users/register", json=user_data)
    assert response.status_code == 201, f"First registration failed: {response.text}"
    
    # Вторая попытка регистрации с тем же email должна завершиться ошибкой
    response = await async_client.post("/api/v1/users/register", json=user_data)
    print(f"Response status: {response.status_code}")
    print(f"Response content: {response.text}")
    
    assert response.status_code == 400, f"Expected 400, got {response.status_code}"
    
    # Проверяем структуру ответа и сообщение об ошибке
    response_data = response.json()
    assert "detail" in response_data, f"Response does not contain 'detail' field: {response_data}"
    assert "уже зарегистрирован" in response_data["detail"], \
        f"Expected error message to contain 'уже зарегистрирован', but got: {response_data['detail']}"
