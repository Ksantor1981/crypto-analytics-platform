import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  vus: 20, // количество виртуальных пользователей
  duration: '30s',
};

export default function () {
  // Тестируем логин (можно заменить на валидные данные)
  let loginRes = http.post('http://localhost:8000/api/v1/users/login', JSON.stringify({
    email: 'test@example.com',
    password: 'test123456',
  }), { headers: { 'Content-Type': 'application/json' } });
  check(loginRes, {
    'login status 200': (r) => r.status === 200,
  });

  let token = loginRes.json('access_token');
  let authHeaders = { headers: { 'Authorization': `Bearer ${token}` } };

  // Тестируем получение каналов
  let channelsRes = http.get('http://localhost:8000/api/v1/channels/', authHeaders);
  check(channelsRes, {
    'channels status 200': (r) => r.status === 200,
  });

  sleep(1);
} 