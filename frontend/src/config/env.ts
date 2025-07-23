// Environment configuration for different stages
export interface AppConfig {
  apiUrl: string;
  wsUrl: string;
  stripePublishableKey: string;
  appName: string;
  appVersion: string;
  environment: 'development' | 'staging' | 'production';
  enableNotifications: boolean;
  enableAnalytics: boolean;
  enableBetaFeatures: boolean;
  debug: boolean;
  gaTrackingId?: string;
  hotjarId?: string;
}

// Get environment variable with fallback
const getEnvVar = (key: string, fallback: string = ''): string => {
  return process.env[key] || fallback;
};

// Get boolean environment variable
const getBoolEnvVar = (key: string, fallback: boolean = false): boolean => {
  const value = process.env[key];
  if (value === undefined) return fallback;
  return value.toLowerCase() === 'true';
};

// Base configuration
const baseConfig: Omit<AppConfig, 'environment'> = {
  apiUrl: getEnvVar('NEXT_PUBLIC_API_URL', 'http://localhost:8000'),
  wsUrl: getEnvVar('NEXT_PUBLIC_WS_URL', 'ws://localhost:8000'),
  stripePublishableKey: getEnvVar('NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY', ''),
  appName: getEnvVar('NEXT_PUBLIC_APP_NAME', 'Crypto Analytics Platform'),
  appVersion: getEnvVar('NEXT_PUBLIC_APP_VERSION', '1.0.0'),
  enableNotifications: getBoolEnvVar('NEXT_PUBLIC_ENABLE_NOTIFICATIONS', true),
  enableAnalytics: getBoolEnvVar('NEXT_PUBLIC_ENABLE_ANALYTICS', true),
  enableBetaFeatures: getBoolEnvVar('NEXT_PUBLIC_ENABLE_BETA_FEATURES', false),
  debug: getBoolEnvVar('NEXT_PUBLIC_DEBUG', false),
  gaTrackingId: getEnvVar('NEXT_PUBLIC_GA_TRACKING_ID'),
  hotjarId: getEnvVar('NEXT_PUBLIC_HOTJAR_ID'),
};

// Environment-specific configurations
const configs: Record<string, AppConfig> = {
  development: {
    ...baseConfig,
    environment: 'development',
    apiUrl: getEnvVar('NEXT_PUBLIC_API_URL', 'http://localhost:8000'),
    wsUrl: getEnvVar('NEXT_PUBLIC_WS_URL', 'ws://localhost:8000'),
    debug: getBoolEnvVar('NEXT_PUBLIC_DEBUG', true),
    enableBetaFeatures: getBoolEnvVar('NEXT_PUBLIC_ENABLE_BETA_FEATURES', true),
  },
  staging: {
    ...baseConfig,
    environment: 'staging',
    apiUrl: getEnvVar('NEXT_PUBLIC_API_URL', 'https://staging-api.crypto-analytics.com'),
    wsUrl: getEnvVar('NEXT_PUBLIC_WS_URL', 'wss://staging-api.crypto-analytics.com'),
    debug: getBoolEnvVar('NEXT_PUBLIC_DEBUG', false),
    enableBetaFeatures: getBoolEnvVar('NEXT_PUBLIC_ENABLE_BETA_FEATURES', true),
  },
  production: {
    ...baseConfig,
    environment: 'production',
    apiUrl: getEnvVar('NEXT_PUBLIC_API_URL', 'https://api.crypto-analytics.com'),
    wsUrl: getEnvVar('NEXT_PUBLIC_WS_URL', 'wss://api.crypto-analytics.com'),
    debug: getBoolEnvVar('NEXT_PUBLIC_DEBUG', false),
    enableBetaFeatures: getBoolEnvVar('NEXT_PUBLIC_ENABLE_BETA_FEATURES', false),
  },
};

// Get current environment
const getCurrentEnvironment = (): 'development' | 'staging' | 'production' => {
  const env = getEnvVar('NEXT_PUBLIC_APP_ENV', 'development');
  if (env === 'staging' || env === 'production') {
    return env;
  }
  return 'development';
};

// Export current configuration
export const config: AppConfig = configs[getCurrentEnvironment()];

// Export individual configs for testing
export const developmentConfig = configs.development;
export const stagingConfig = configs.staging;
export const productionConfig = configs.production;

// Utility functions
export const isDevelopment = () => config.environment === 'development';
export const isStaging = () => config.environment === 'staging';
export const isProduction = () => config.environment === 'production';

// Validation function
export const validateConfig = (): string[] => {
  const errors: string[] = [];
  
  if (!config.apiUrl) {
    errors.push('API URL is required');
  }
  
  if (!config.wsUrl) {
    errors.push('WebSocket URL is required');
  }
  
  if (isProduction() && !config.stripePublishableKey) {
    errors.push('Stripe publishable key is required in production');
  }
  
  if (config.enableAnalytics && !config.gaTrackingId && isProduction()) {
    errors.push('Google Analytics tracking ID is required when analytics is enabled in production');
  }
  
  return errors;
};

// Log configuration on startup (development only)
if (isDevelopment() && typeof window !== 'undefined') {
  console.log('🔧 App Configuration:', config);
  
  const validationErrors = validateConfig();
  if (validationErrors.length > 0) {
    console.warn('⚠️ Configuration warnings:', validationErrors);
  }
}
