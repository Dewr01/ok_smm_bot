# 🚀 Запуск OK SMM Combiner через Docker

## 1. Собрать контейнер
```bash
docker-compose build
```

## 2. Запустить
```bash
docker-compose up -d
```

## 3. Проверить
Админка будет доступна на:
http://localhost:5010/admin

## 4. Логи
```bash
docker logs -f ok_smm_bot
```

## 5. Обновить
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```
