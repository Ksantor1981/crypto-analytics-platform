import http from 'k6/http';
import { check, sleep } from 'k6';

const BASE_URL = (__ENV.BASE_URL || 'http://localhost:8000').replace(/\/$/, '');
const TARGET_RPS = Number(__ENV.TARGET_RPS || 100);
const DURATION = __ENV.DURATION || '2m';
const PRE_ALLOCATED_VUS = Number(__ENV.PRE_ALLOCATED_VUS || Math.max(20, TARGET_RPS / 2));
const MAX_VUS = Number(__ENV.MAX_VUS || Math.max(100, TARGET_RPS * 2));
const AUTH_TOKEN = __ENV.AUTH_TOKEN || '';
const SUMMARY_DIR = (__ENV.K6_SUMMARY_DIR || 'docs/load-test-artifacts').replace(/\/$/, '');

export const options = {
  scenarios: {
    staging_read_path: {
      executor: 'constant-arrival-rate',
      rate: TARGET_RPS,
      timeUnit: '1s',
      duration: DURATION,
      preAllocatedVUs: PRE_ALLOCATED_VUS,
      maxVUs: MAX_VUS,
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.01'],
    'http_req_duration{kind:read}': ['p(95)<200'],
    checks: ['rate>0.99'],
  },
};

const publicEndpoints = [
  '/health',
  '/api/v1/channels/',
  '/',
];

const privateEndpoints = [
  '/api/v1/signals/dashboard',
  '/api/v1/channels/dashboard/',
];

function authHeaders() {
  return AUTH_TOKEN ? { Authorization: `Bearer ${AUTH_TOKEN}` } : {};
}

export default function () {
  const publicPath = publicEndpoints[__ITER % publicEndpoints.length];
  const publicRes = http.get(`${BASE_URL}${publicPath}`, {
    tags: { kind: 'read', endpoint: publicPath },
  });
  check(publicRes, {
    [`${publicPath} returns 2xx/3xx/401/403`]: (r) =>
      (r.status >= 200 && r.status < 400) || r.status === 401 || r.status === 403,
  });

  if (AUTH_TOKEN) {
    const privatePath = privateEndpoints[__ITER % privateEndpoints.length];
    const privateRes = http.get(`${BASE_URL}${privatePath}`, {
      headers: authHeaders(),
      tags: { kind: 'read', endpoint: privatePath },
    });
    check(privateRes, {
      [`${privatePath} authenticated read ok`]: (r) => r.status >= 200 && r.status < 400,
    });
  }

  sleep(0.05);
}

function value(data, metric, name) {
  return data.metrics[metric]?.values?.[name] ?? null;
}

function markdownSummary(data) {
  const p95 = value(data, 'http_req_duration', 'p(95)');
  const failRate = value(data, 'http_req_failed', 'rate');
  const checksRate = value(data, 'checks', 'rate');
  const reqs = value(data, 'http_reqs', 'count');
  const rps = value(data, 'http_reqs', 'rate');

  return [
    '# k6 staging proof',
    '',
    `- Base URL: ${BASE_URL}`,
    `- Target RPS: ${TARGET_RPS}`,
    `- Duration: ${DURATION}`,
    `- Requests: ${reqs ?? 'n/a'}`,
    `- Actual RPS: ${rps != null ? rps.toFixed(2) : 'n/a'}`,
    `- p95 latency: ${p95 != null ? `${p95.toFixed(2)} ms` : 'n/a'}`,
    `- Failure rate: ${failRate != null ? `${(failRate * 100).toFixed(2)}%` : 'n/a'}`,
    `- Check pass rate: ${checksRate != null ? `${(checksRate * 100).toFixed(2)}%` : 'n/a'}`,
    '',
    'Thresholds:',
    '- `http_req_failed < 1%`',
    '- `http_req_duration{kind:read} p95 < 200ms`',
    '- `checks > 99%`',
    '',
  ].join('\n');
}

export function handleSummary(data) {
  return {
    stdout: markdownSummary(data),
    [`${SUMMARY_DIR}/k6-staging-summary.json`]: JSON.stringify(data, null, 2),
    [`${SUMMARY_DIR}/k6-staging-summary.md`]: markdownSummary(data),
  };
}
