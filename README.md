[![Foodgram workflow](https://github.com/illusory-code/foodgram/actions/workflows/main.yml/badge.svg)](https://github.com/illusory-code/foodgram/actions/workflows/main.yml)
## Проект: [Foodgram](https://foodgramkuzmin.zapto.org/)
#### Итоговая работа *Яндекс.Практикум* (backend-часть)

Foodgram — это онлайн-платформа, где пользователи могут делиться кулинарными рецептами, добавлять понравившиеся рецепты в избранное и следить за обновлениями других авторов. Для зарегистрированных пользователей доступна функция «Корзина покупок», которая автоматически формирует список необходимых ингредиентов для выбранных блюд.

### Используемый стек
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white)
![Django REST Framework](https://img.shields.io/badge/DRF-092E20?style=for-the-badge&logo=django&logoColor=white)
![Djoser](https://img.shields.io/badge/Djoser-092E20?style=for-the-badge&logo=django&logoColor=white)
![Gunicorn](https://img.shields.io/badge/Gunicorn-499848?style=for-the-badge&logo=gunicorn&logoColor=white)
![Nginx](https://img.shields.io/badge/Nginx-009639?style=for-the-badge&logo=nginx&logoColor=white)
![React](https://img.shields.io/badge/React-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?style=for-the-badge&logo=github-actions&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![Postman](https://img.shields.io/badge/Postman-FF6C37?style=for-the-badge&logo=postman&logoColor=white)

### Развертывание проекта локально

1. Скопируйте репозиторий на локальную машину:
```bash
git clone https://github.com/illusory-code/foodgram.git
cd foodgram/backend
```

2. Создайте и активируйте виртуальное окружение (Linux):
```bash
python -m venv venv
source venv/bin/activate
```
Для Windows:
```bash
python -m venv venv
source venv/Scripts/activate
```

3. Обновите pip и установите зависимости:
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

4. Примените миграции:
```bash
python manage.py migrate
```

5. Создайте администратора:
```bash
python manage.py createsuperuser
```

6. Соберите статические файлы:
```bash
python manage.py collectstatic --no-input
```

7. Наполните базу тестовыми данными:
```bash
python manage.py load_db
```

8. Запустите сервер разработки:
```bash
python manage.py runserver
```

Проект будет доступен локально с настройками debug=True и SQLite.

### Полноценный запуск в контейнерах

Для работы всех сервисов потребуются Docker и Docker Compose.

Установка Docker:
- [Docker Desktop для Windows/MacOS](https://www.docker.com/products/docker-desktop)
- [Docker Engine для Linux](https://docs.docker.com/engine/install/ubuntu/) + [Docker Compose](https://docs.docker.com/compose/install/)

### Деплой на удаленный сервер

1. Установка Docker на сервере (Ubuntu):
```bash
sudo apt update
sudo apt install curl
curl -fSL https://get.docker.com -o get-docker.sh
sudo sh ./get-docker.sh
sudo apt-get install docker-compose-plugin
```

2. Перенесите файл [docker-compose.production.yml](https://github.com/illusory-code/foodgram/blob/main/docker-compose.production.yml) на сервер, адаптировав под свои параметры.

3. Создайте в директории с docker-compose файл **.env** со следующими переменными:
```bash
POSTGRES_DB=название_бд
POSTGRES_USER=пользователь_бд
POSTGRES_PASSWORD=пароль_бд
DB_HOST=db
DB_PORT=5432
SECRET_KEY=секретный_ключ_django
DEBUG=False
ALLOWED_HOSTS=ваш_домен.ру
```

4. Запустите контейнеры:
```bash
sudo docker compose -f docker-compose.production.yml up -d
```

5. Настройте Nginx на сервере:
- Откройте конфигурационный файл:
```bash
sudo nano /etc/nginx/sites-enabled/default
```

- Добавьте конфигурацию, подставив ваш домен:
```nginx
server {
    listen 80;
    server_name ваш-домен.ру;

    location / {
        proxy_set_header Host $http_host;
        proxy_pass http://127.0.0.1:9001;
        client_max_body_size 5M;
    }
}
```

- Проверьте корректность конфигурации и перезагрузите Nginx:
```bash
sudo nginx -t
sudo service nginx reload
```

#### Разработчик: [Кузьмин Владимир](https://github.com/illusory-code)
```