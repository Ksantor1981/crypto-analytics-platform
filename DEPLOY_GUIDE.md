# Production Deploy Guide: Crypto Analytics Platform

## 1. Требования к окружению
- Kubernetes 1.24+
- Helm 3.x
- Docker (для сборки образов)
- Доступ к приватному/публичному Docker Registry (если образы не локальные)
- (Рекомендуется) Prometheus и Grafana для мониторинга

## 2. Сборка Docker-образов
Выполните в корне проекта:
```bash
docker build -t crypto-analytics-backend:latest ./backend
docker build -t crypto-analytics-frontend:latest ./frontend
docker build -t crypto-analytics-ml-service:latest ./ml-service
docker build -t crypto-analytics-workers:latest ./workers
```

Загрузите образы в ваш registry, если требуется:
```bash
docker tag crypto-analytics-backend:latest <your-registry>/crypto-analytics-backend:latest
docker push <your-registry>/crypto-analytics-backend:latest
# Аналогично для остальных сервисов
```

## 3. Установка Helm-чарта
```bash
cd helm
helm install crypto-analytics .
```

Для обновления:
```bash
helm upgrade crypto-analytics .
```

## 4. Проверка статуса сервисов
```bash
kubectl get pods
kubectl get svc
kubectl get ingress
```

## 5. Настройка Ingress и DNS
- Проверьте, что Ingress создан (`kubectl get ingress`).
- Пропишите DNS или /etc/hosts:
  ```
  127.0.0.1 crypto-analytics.local
  ```
- Для minikube:
  ```bash
  minikube tunnel
  ```

## 6. Мониторинг (Prometheus + Grafana)
- Примените `monitoring/prometheus.yml` для Prometheus.
- Импортируйте дашборды из `monitoring/grafana-dashboards/` в Grafana.
- Проверьте, что метрики собираются для всех сервисов.

## 7. Security Audit
- Запустите аудит локально:
  ```bash
  ./security_audit.sh
  ```
- Аудит также запускается автоматически в CI/CD (см. GitHub Actions).
- Ознакомьтесь с результатами и устраните критические уязвимости.

## 8. Troubleshooting
- Проверяйте логи pod'ов:
  ```bash
  kubectl logs <pod-name>
  ```
- Проверяйте состояние ingress и сервисов:
  ```bash
  kubectl describe ingress
  kubectl describe svc <service-name>
  ```
- Для проблем с миграциями БД — проверьте переменные окружения и логи backend.

## 9. Обновление и откат
- Для обновления:
  ```bash
  helm upgrade crypto-analytics .
  ```
- Для отката:
  ```bash
  helm rollback crypto-analytics <revision>
  ```

## 10. CI/CD и автоматизация
- Все ключевые проверки (линтинг, тесты, security audit, сборка Docker) автоматизированы через GitHub Actions.
- Рекомендуется интегрировать деплой в staging/production через отдельный workflow (см. примеры в .github/workflows/).

---

**Вопросы и предложения по улучшению — в ISSUE трекер проекта.** 