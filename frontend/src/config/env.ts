interface Environment {
  NEXT_PUBLIC_API_URL: string;
  NEXT_PUBLIC_ML_URL: string;
  NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY: string;
  NEXT_PUBLIC_ENVIRONMENT: 'development' | 'production' | 'staging';
}

export const env: Environment = {
  NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1',
  NEXT_PUBLIC_ML_URL: process.env.NEXT_PUBLIC_ML_URL || 'http://localhost:8001/api/v1',
  NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY: process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY || '',
  NEXT_PUBLIC_ENVIRONMENT: (process.env.NEXT_PUBLIC_ENVIRONMENT || 'development') as Environment['NEXT_PUBLIC_ENVIRONMENT']
};
