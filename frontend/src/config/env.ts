interface Environment {
  NEXT_PUBLIC_API_URL: string;
  NEXT_PUBLIC_ML_URL: string;
  NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY: string;
  NEXT_PUBLIC_ENVIRONMENT: 'development' | 'production' | 'staging';
}

/**
 * Единая база для fetch к FastAPI: всегда с суффиксом /api/v1.
 * В .env часто задают только хост (http://localhost:8000) — без этого пути вида
 * /users/me и /stripe/create-checkout уходят на неверные URL.
 */
export function normalizePublicApiUrl(raw: string): string {
  const t = raw.trim().replace(/\/$/, '');
  if (t.endsWith('/api/v1')) return t;
  return `${t}/api/v1`;
}

export const env: Environment = {
  NEXT_PUBLIC_API_URL: normalizePublicApiUrl(
    process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
  ),
  NEXT_PUBLIC_ML_URL:
    process.env.NEXT_PUBLIC_ML_URL || 'http://localhost:8001/api/v1',
  NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY:
    process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY || '',
  NEXT_PUBLIC_ENVIRONMENT: (process.env.NEXT_PUBLIC_ENVIRONMENT ||
    'development') as Environment['NEXT_PUBLIC_ENVIRONMENT'],
};
