# Телеметрия и мониторинг

## Дашборды MAU/WAU/DAU

- **DAU** — количество уникальных пользователей за последние 24 часа:
  ```sql
  SELECT COUNT(DISTINCT user_id)
  FROM events
  WHERE event = 'start' AND ts >= NOW() - INTERVAL '1 day';
  ```
- **WAU** — активность за 7 дней:
  ```sql
  SELECT COUNT(DISTINCT user_id)
  FROM events
  WHERE event = 'start' AND ts >= NOW() - INTERVAL '7 days';
  ```
- **MAU** — активность за 30 дней:
  ```sql
  SELECT COUNT(DISTINCT user_id)
  FROM events
  WHERE event = 'start' AND ts >= NOW() - INTERVAL '30 days';
  ```
Эти запросы можно подключить в Grafana через Data Source PostgreSQL. Графики строятся по расписанию с шагом в сутки.

## Алёрты

Рекомендуемые правила Prometheus:

- `http_request_duration_seconds_bucket{le="0.5"}` — отслеживать процент запросов быстрее 0.5 с; при падении ниже 95 % отправлять предупреждение.
- `http_requests_total{status=~"5.."}` — срабатывает при появлении ответов 5xx.
- `verifier_fail_pct` из `/admin/metrics` — алёрт при превышении 5 % неуспешных проверок.
- Отсутствие новых событий `start` более 10 минут сигнализирует о простое бота.

Система оповещений может отправлять уведомления в Telegram или Slack через Alertmanager.
