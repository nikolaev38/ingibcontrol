import pytest
import time
from fastapi import status

class TestAuthAPI:
    """Тесты для API аутентификации."""

    @pytest.mark.asyncio
    async def test_api(self, client):
        """
        Тест регистрации и аутентификации зарегистрированных
        и не зарегистрированных пользователей.
        """

        """Тест аутентификации не зарегистрированного пользователя."""
        response_cookie = client.get("/api_site/v1/auth/cookies-session")
        data_response_cookie = response_cookie.json()
        print(data_response_cookie)
        assert response_cookie.status_code == status.HTTP_200_OK, "Cookie недоступен"
        assert "new_session_id" in data_response_cookie, "Cookie не содержит session_id"

        # Создаем нового клиента с установленными cookies
        session_id = data_response_cookie["new_session_id"]
    
        # Обновляем клиент с установленными cookies
        client.cookies.set("session_id", session_id)
    
        # Делаем запросы с тем же клиентом, чтобы сохранялись cookies
        response_cookie_update_1 = client.get("/api_site/v1/auth/cookies-session")
        response_cookie_update_2 = client.get("/api_site/v1/auth/cookies-session")
        
        data_response_cookie_update = response_cookie_update_2.json()
        print(data_response_cookie_update)
        
        assert response_cookie_update_1.status_code == status.HTTP_200_OK, "Cookie недоступен"
        assert response_cookie_update_2.status_code == status.HTTP_200_OK, "Cookie недоступен"
        assert "new_session_id" in data_response_cookie_update, "Cookie не содержит session_id"


        """Тест регистрации и аутентификации зарегистрированного пользователя."""
        # Подготовка тестовых данных
        test_email = f"test_register_{int(time.time())}@example.com"
        test_password = "TestPass123!"
        
        # Регистрируем нового пользователя
        response = client.post(
            "/api_site/v1/auth/register",
            data={
                "email": test_email,
                "password": test_password
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Cookie-Session": "test-session"
            }
        )
        
        # Проверяем успешную регистрацию (ожидаем 200 вместо 201)
        assert response.status_code == status.HTTP_200_OK, \
            f"Ожидался статус 200, получен {response.status_code}. Ответ: {response.text}"
        
        # Проверяем ответ
        data = response.json()
        print(data)
        assert "access_token" in data, "В ответе отсутствует access_token"
        assert "refresh_token" in data, "В ответе отсутствует refresh_token"
        assert "token_type" in data, "В ответе отсутствует token_type"
        assert data["token_type"] == "Bearer", "Неверный тип токена"
        
        # Проверяем, что повторная регистрация с тем же email невозможна
        response = client.post(
            "/api_site/v1/auth/register",
            data={
                "email": test_email,
                "password": "AnotherPassword123!"
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Cookie-Session": "test-session"
            }
        )
        assert response.status_code == status.HTTP_409_CONFLICT, \
            "Повторная регистрация с тем же email должна быть запрещена"
        
        response_login = client.post(
            "/api_site/v1/auth/login",
            data={
                "email": test_email,
                "password": test_password
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Cookie-Session": "test-session"
            }
        )
        assert response_login.status_code == status.HTTP_200_OK, \
            f"Ожидался статус 200, получен {response_login.status_code}. Ответ: {response_login.text}"
        
        data_login = response_login.json()
        print(data_login)

        assert "access_token" in data_login, "В ответе отсутствует access_token"
        assert "refresh_token" in data_login, "В ответе отсутствует refresh_token"
        assert "token_type" in data_login, "В ответе отсутствует token_type"
        assert data_login["token_type"] == "Bearer", "Неверный тип токена"
        
        response_me = client.get(
            "/api_site/v1/auth/me",
            headers={
                "Authorization": f"Bearer {data_login['access_token']}",
                "Cookie-Session": "test-session"
            }
        )
        assert response_me.status_code == status.HTTP_200_OK, \
            f"Ожидался статус 200, получен {response_me.status_code}. Ответ: {response_me.text}"
        
        data_me = response_me.json()
        print(data_me)
        assert "email" in data_me, "В ответе отсутствует email"
        assert "role" in data_me, "В ответе отсутствует role"

        response_refresh = client.post(
            "/api_site/v1/auth/refresh",
            headers={
                "Authorization": f"Bearer {data_login['refresh_token']}",
                "Cookie-Session": "test-session"
            }
        )
        assert response_refresh.status_code == status.HTTP_200_OK, \
            f"Ожидался статус 200, получен {response_refresh.status_code}. Ответ: {response_refresh.text}"
        
        data_refresh = response_refresh.json()
        print(data_refresh)
        assert "access_token" in data_refresh, "В ответе отсутствует access_token"
        assert "refresh_token" in data_refresh, "В ответе отсутствует refresh_token"
        assert "token_type" in data_refresh, "В ответе отсутствует token_type"
        assert data_refresh["token_type"] == "Bearer", "Неверный тип токена"
        
        