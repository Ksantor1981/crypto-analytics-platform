/**
 * k6 load test for Crypto Analytics Platform API.
 * Target: 1000 RPS (per ТЗ), API <200ms.
 * Run: k6 run scripts/load-test/k6-load.js
 * Options: k6 run --vus 50 --duration 30s scripts/load-test/k6-load.js
 */
import http from 'k6/http';
import { check, sleep } from 'k6';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

export const options = {
  vus: 20,
  duration: '30s',
  thresholds: {
    http_req_duration: ['p(95)<200'],  // 95% of requests < 200ms (per ТЗ)
    http_req_failed: ['rate<0.01'],
  },
};

export default function () {
  const urls = [
    `${BASE_URL}/`,
    `${BASE_URL}/health`,
    `${BASE_URL}/api/v1/channels/`,
    `${BASE_URL}/api/v1/dashboard/`,
  ];

  for (const url of urls) {
    const res = http.get(url);
    check(res, {
      [`${url} status 200`]: (r) => r.status === 200 || r.status === 401,
      [`${url} duration < 500ms`]: (r) => r.timings.duration < 500,
    });
    sleep(0.1);
  }
}
