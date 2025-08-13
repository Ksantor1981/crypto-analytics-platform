# 🔗 API Client Setup Guide - Исправление интеграции frontend ↔ backend

**Проблема:** Frontend не подключен к backend API  
**Решение:** Современный TypeScript API клиент с полной интеграцией  
**Статус:** ✅ ГОТОВ К ТЕСТИРОВАНИЮ

---

## 📦 Что создано:

### ✅ **Основные файлы:**
- `frontend/src/lib/api.ts` - Современный API клиент
- `frontend/src/contexts/AuthContext.tsx` - Контекст авторизации  
- `frontend/src/pages/test-login.tsx` - Страница тестирования API
- `frontend/src/types/api.ts` - TypeScript типы
- `frontend/src/hooks/useApiCall.ts` - Кастомные React хуки

### ✅ **Обновленные файлы:**
- `frontend/next.config.js` - добавлены proxy и env переменные
- `frontend/src/pages/_app.tsx` - уже содержал AuthProvider

---

## 🚀 Инструкция по запуску:

### 1. **Создайте .env.local файл**
```bash
# В папке frontend/ создайте файл .env.local
cd frontend
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
echo "NEXT_PUBLIC_ML_API_URL=http://localhost:8001" >> .env.local
echo "NEXT_PUBLIC_ENV=development" >> .env.local
```

### 2. **Запустите backend сервисы**
```bash
# В корне проекта
docker-compose up -d
# Или
docker-compose up backend ml-service postgres redis
```

### 3. **Запустите frontend**
```bash
cd frontend
npm run dev
```

### 4. **Протестируйте API интеграцию**
Откройте в браузере: **http://localhost:3000/test-login**

---

## 🧪 Тестирование API клиента:

### **Страница тестирования:** `/test-login`

**Что можно протестировать:**
1. **API Connection** - проверка подключения к backend
2. **Authentication** - тестовый логин пользователя  
3. **ML Service** - проверка ML предсказаний
4. **Console debugging** - логирование API клиента

### **Тестовые данные:**
- Email: `test@example.com`  
- Password: `password123`

*(Если такого пользователя нет, создайте через backend API)*

---

## 💻 Как использовать в компонентах:

### **1. Простые API вызовы:**
```typescript
import apiClient from '@/lib/api';

// Где угодно в компонентах
const channels = await apiClient.getChannels();
const prediction = await apiClient.getPrediction({
  symbol: 'BTCUSDT',
  signal_type: 'LONG', 
  entry_price: 50000
});
```

### **2. Авторизация:**
```typescript
import { useAuth } from '@/contexts/AuthContext';

function LoginComponent() {
  const { login, isAuthenticated, user } = useAuth();
  
  const handleLogin = async () => {
    const success = await login('email@test.com', 'password');
    if (success) {
      // Перенаправление или обновление UI
    }
  };
}
```

### **3. React хуки:**
```typescript
import { useChannels, useSignals } from '@/hooks/useApiCall';

function ChannelsPage() {
  const { data: channels, loading, error } = useChannels(1, 20);
  const { data: signals } = useSignals();
  
  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  
  return <div>{channels?.map(ch => ch.name)}</div>;
}
```

---

## 🔧 Возможности API клиента:

### **✅ Автоматические функции:**
- **Retry logic** - повторные попытки при сетевых ошибках
- **Token refresh** - автообновление access токенов
- **Error handling** - обработка 401, 500, network errors
- **Request timeout** - защита от зависших запросов
- **LocalStorage** - автосохранение токенов авторизации

### **✅ Поддерживаемые эндпоинты:**
- **Authentication**: login, register, logout, getCurrentUser
- **Channels**: getChannels, getChannel, subscribeToChannel  
- **Signals**: getSignals, getSignal
- **ML Predictions**: getPrediction, testPrediction
- **Subscriptions**: getSubscriptions, updateSubscription
- **Trading**: getTradingStatus, startTrading, stopTrading

---

## 🐛 Диагностика проблем:

### **Проблема: "API connection failed"**
```bash
# Проверьте что backend запущен
curl http://localhost:8000/health

# Проверьте переменные окружения
echo $NEXT_PUBLIC_API_URL
```

### **Проблема: "401 Unauthorized"**
```typescript
// В DevTools Console
apiClient.clearTokens();
// Затем заново залогиньтесь
```

### **Проблема: "CORS errors"**
- Убедитесь что backend настроен на CORS для `http://localhost:3000`
- Проверьте настройки в `backend/app/main.py`

### **Debugging в Console:**
```javascript
// В браузере DevTools → Console
apiClient.testConnection();
apiClient.healthCheck();
console.log('Auth status:', apiClient.isAuthenticated());
```

---

## 📊 Архитектурные преимущества:

### **✅ Type Safety:**
- Все API ответы типизированы TypeScript
- IntelliSense подсказки в IDE
- Compile-time проверка ошибок

### **✅ Error Resilience:**
- Автоматический retry при network errors
- Graceful handling 401/403/500 ошибок  
- Timeout protection

### **✅ Developer Experience:**
- Простой API: `await apiClient.getChannels()`
- React хуки: `useChannels(), useSignals()`
- Debugging: console логи и error messages

### **✅ Production Ready:**
- Token refresh механизм
- Secure token storage
- Environment configuration
- Proxy support для production

---

## 🎯 Следующие шаги:

1. **Протестируйте** API клиент на странице `/test-login`
2. **Замените** старые API вызовы в существующих компонентах
3. **Создайте** необходимые страницы: dashboard, channels, signals
4. **Настройте** production environment variables

---

## 💡 Tips & Best Practices:

### **Использование в страницах:**
```typescript
// pages/channels.tsx
export default function ChannelsPage() {
  const { data, loading, error } = useChannels();
  // Автоматическая загрузка при монтировании
}
```

### **Обработка ошибок:**
```typescript
const response = await apiClient.getChannels();
if (response.error) {
  // Показать toast или alert
  alert(`Error: ${response.error}`);
} else {
  // Использовать response.data
  setChannels(response.data);
}
```

### **Loading states:**
```typescript
const { data, loading, error, refetch } = useChannels();

return (
  <div>
    {loading && <Spinner />}
    {error && <ErrorMessage error={error} onRetry={refetch} />}
    {data && <ChannelsList channels={data} />}
  </div>
);
```

---

**✅ API клиент готов! Теперь frontend может полноценно взаимодействовать с backend!** 🚀
