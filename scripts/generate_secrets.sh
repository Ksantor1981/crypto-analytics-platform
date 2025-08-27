#!/bin/bash

# Generate secure secrets for production deployment
# Run this script to generate all required secrets

echo "🔐 Generating production secrets..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Generate secrets
SECRET_KEY=$(openssl rand -hex 32)
TRADING_ENCRYPTION_KEY=$(openssl rand -hex 32)
POSTGRES_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
REDIS_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
JWT_SECRET=$(openssl rand -hex 32)

# Create .env.production file
cat > .env.production << EOF
# Generated secrets for production - $(date)
# Keep this file secure and never commit to git!

# ===== SECURITY (GENERATED) =====
SECRET_KEY=${SECRET_KEY}
TRADING_ENCRYPTION_KEY=${TRADING_ENCRYPTION_KEY}
JWT_SECRET=${JWT_SECRET}

# ===== DATABASE (GENERATED) =====
POSTGRES_USER=postgres
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@postgres:5432/crypto_analytics

# ===== REDIS (GENERATED) =====
REDIS_PASSWORD=${REDIS_PASSWORD}
REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0

# ===== DOMAINS (UPDATE THESE!) =====
FRONTEND_URL=https://crypto-analytics.yourdomain.com
BACKEND_URL=https://api.yourdomain.com
ML_SERVICE_URL=https://ml.yourdomain.com
BACKEND_CORS_ORIGINS=https://crypto-analytics.yourdomain.com,https://app.yourdomain.com

# ===== TELEGRAM API (SET THESE!) =====
TELEGRAM_API_ID=your_telegram_api_id_here
TELEGRAM_API_HASH=your_telegram_api_hash_here
TELEGRAM_SESSION_NAME=crypto_analytics_production

# ===== EXTERNAL APIS (SET THESE!) =====
COINGECKO_API_KEY=your_coingecko_api_key_here
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_SECRET_KEY=your_binance_secret_key_here

# ===== PAYMENT PROCESSING (SET THESE!) =====
STRIPE_PUBLISHABLE_KEY=pk_live_your_stripe_publishable_key_here
STRIPE_SECRET_KEY=sk_live_your_stripe_secret_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here

# ===== EMAIL CONFIGURATION (SET THESE!) =====
EMAIL_SMTP_HOST=smtp.yourmailprovider.com
EMAIL_SMTP_PORT=587
EMAIL_SMTP_USERNAME=your_email@yourdomain.com
EMAIL_SMTP_PASSWORD=your_email_password_here
EMAIL_FROM_ADDRESS=noreply@yourdomain.com
EMAIL_FROM_NAME=Crypto Analytics Platform

# ===== MONITORING (OPTIONAL) =====
SENTRY_DSN=https://your_sentry_dsn@sentry.io/project_id
PROMETHEUS_URL=http://prometheus:9090
GRAFANA_URL=http://grafana:3001

# ===== PORTS =====
BACKEND_PORT=8000
FRONTEND_PORT=3000
ML_SERVICE_PORT=8001
POSTGRES_PORT=5432
REDIS_PORT=6379

EOF

echo -e "${GREEN}✅ Generated .env.production file${NC}"
echo ""
echo -e "${YELLOW}⚠️  IMPORTANT SECURITY NOTES:${NC}"
echo -e "${RED}1. Never commit .env.production to git!${NC}"
echo -e "${RED}2. Update the placeholder values marked with 'SET THESE!'${NC}"
echo -e "${RED}3. Update yourdomain.com to your actual domain${NC}"
echo ""
echo -e "${YELLOW}📝 Generated secrets:${NC}"
echo -e "SECRET_KEY: ${GREEN}${SECRET_KEY}${NC}"
echo -e "POSTGRES_PASSWORD: ${GREEN}${POSTGRES_PASSWORD}${NC}"
echo -e "REDIS_PASSWORD: ${GREEN}${REDIS_PASSWORD}${NC}"
echo ""
echo -e "${YELLOW}🔧 Next steps:${NC}"
echo "1. Edit .env.production and fill in all 'SET THESE!' values"
echo "2. Update domain names from yourdomain.com to your actual domain"
echo "3. Get SSL certificates for your domain"
echo "4. Run: docker-compose -f docker-compose.production.yml up -d"
echo ""
echo -e "${GREEN}🎯 Production secrets generated successfully!${NC}"

# Make sure the file is not readable by others
chmod 600 .env.production

# Add to .gitignore if not already there
if ! grep -q ".env.production" .gitignore 2>/dev/null; then
    echo ".env.production" >> .gitignore
    echo -e "${GREEN}✅ Added .env.production to .gitignore${NC}"
fi
