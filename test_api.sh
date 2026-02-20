#!/bin/bash

BASE_URL="http://localhost:8000/api"
TOKEN=""

echo "=== Тестирование API Foodgram ==="

# 1. Получение токена
echo "1. Получение токена..."
TOKEN=$(curl -s -X POST "$BASE_URL/auth/token/login/" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test123!"
  }' | jq -r '.auth_token')

echo "Токен: $TOKEN"

# 2. Получение списка рецептов
echo -e "\n2. Получение списка рецептов..."
curl -s "$BASE_URL/recipes/" | jq '.'

# 3. Получение списка тегов
echo -e "\n3. Получение списка тегов..."
curl -s "$BASE_URL/tags/" | jq '.'

# 4. Получение списка ингредиентов
echo -e "\n4. Получение списка ингредиентов..."
curl -s "$BASE_URL/ingredients/?name=томат" | jq '.'

# 5. Добавление в избранное (если есть рецепты)
echo -e "\n5. Добавление в избранное..."
curl -s -X POST "$BASE_URL/recipes/1/favorite/" \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json"

# 6. Добавление в корзину
echo -e "\n6. Добавление в корзину..."
curl -s -X POST "$BASE_URL/recipes/1/shopping_cart/" \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json"

echo -e "\n=== Тестирование завершено ==="
