# TaskManagerPy

> Система управления задачами с ролевой моделью доступа для «Начальник» — «Подчинённый».

[**Django**](https://www.djangoproject.com/) 6.1.1 · [**SQLite**](https://www.sqlite.org/) · [**Bootstrap 5**](https://getbootstrap.com/) · **Python 3**

---

## Содержание

1. [Возможности](#возможности)
2. [Архитектура проекта](#архитектура-проекта)
3. [Установка и запуск](#установка-и-запуск)
4. [Роли и права доступа](#роли-и-права-доступа)
5. [Модель данных](#модель-данных)
6. [Маршруты (URLs)](#маршруты-urls)
7. [Конфигурация](#конфигурация)
8. [Шаблоны и статика](#шаблоны-и-статика)
9. [Технические детали](#технические-детали)

---

## Возможности

| Возможность | Описание |
|---|---|
| **Ролевой доступ (RBAC)** | Два роли: **Начальник** и **Подчинённый**, реализованные через Django Groups. |
| **Полный CRUD задач** | Создание, просмотр, редактирование и удаление задач (только для начальника). |
| **Назначение исполнителей** | Начальник выбирает подчинённого при создании / редактировании задачи. |
| **Смена статуса** | Подчинённый и начальник (если назначен исполнителем) могут отметить задачу как выполненную / не выполненную. |
| **Фильтрация по ролям** | Подчинённый видит **только свои** задачи; начальник видит **только свои задачи и назначенные на него**. |
| **Управление пользователями** | Начальник может создавать учётные записи начальника и подчинённых (автоматическое назначение группы). |
| **Уведомления (Flash Messages)** | Success / Error / Info / Warning уведомления через Django messages framework. |
| **Bootstrap 5 UI** | Адаптивный интерфейс на основе карточной сетки. |
| **Безопасность** | CSRF, secure session/CSRF cookies в production, заголовок `SECURE_SSL_REDIRECT`, заголовок `X-Content-Type-Options`. |

---

## Архитектура проекта

```
taskmanager/
├── .env                          # Переменные окружения (SECRET_KEY, DEBUG, ALLOWED_HOSTS)
├── .gitignore                    # venv/, __pycache__, .env, db.sqlite3, media/
├── manage.py                     # Entry point Django CLI
├── db.sqlite3                    # База данных (создаётся автоматически)
├── venv/                         # Виртуальное окружение Python
├── core/                         # Основное Django-приложение
│   ├── apps.py                   # CoreConfig(AppConfig)
│   ├── models.py                 # Модель Task
│   ├── views.py                  # View-классы (CRUD + управление пользователями)
│   ├── forms.py                  # TaskForm, StatusForm, BossUserCreateForm, EmployeeUserCreateForm
│   ├── admin.py                  # Регистрация Task в Django Admin
│   ├── urls.py                   # Маршруты приложения core
│   ├── templatetags/roles.py     # Кастомный фильтр: has_group(user, group_name)
│   ├── migrations/               # 4 миграции (Task → добавление executor)
│   ├── templates/core/           # Шаблон Django
│   │   ├── base.html             # Базовый лейаут с хедером и уведомлениями
│   │   ├── login.html            # Страница входа
│   │   ├── task_list.html        # Сетка задач
│   │   ├── task_detail.html      # Детали задачи
│   │   ├── task_form.html        # Создание и редактирование задачи
│   │   ├── task_confirm_delete.html
│   │   └── user_create_form.html # Единая форма для boss/employee
│   └── static/css/               # Стили
│       ├── base.css
│       ├── task_list.css
│       ├── task_detail.css
│       ├── task_form.css
│       └── login.css
└── taskmanager/                  # Конфигурация проекта
    ├── settings.py               # DJANGO settings
    ├── urls.py                   # Root URLconf
    ├── wsgi.py / asgi.py
```

---

## Установка и запуск

### 1. Клонирование

```bash
git clone <repository-url>
cd taskmanager
```

### 2. Виртуальное окружение

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Установка зависимостей

Зависимости устанавливаются непосредственно в `venv` (файл `requirements.txt` отсутствует). Основные пакеты:

- `Django>=6.1.1`
- `django-crispy-forms`
- `crispy-bootstrap5`
- `python-dotenv`

### 4. Переменные окружения

Создайте файл `.env` в корне проекта:

```env
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
```

### 5. Миграции и суперпользователь

```bash
python manage.py migrate
python manage.py createsuperuser
```

### 6. Запуск сервера

```bash
python manage.py runserver
```

Проект доступен по адресу: `http://127.0.0.1:8000/`

---

## Роли и права доступа

Проект использует **Django Groups** (без кастомной User-модели) для разделения прав.

### Начальник (`Group: "Начальник"`)

- Видит **только свои задачи и назначенные на него** (где `author` или `executor`)
- Создаёт / редактирует / удаляет задачи
- Назначает исполнителей
- Меняет статус задачи, если он назначен исполнителем
- Создаёт новые учётные записи (начальников и подчинённых)
- Доступ к админ-панели (`/admin/`)

### Подчинённый (`Group: "Подчинённый"`)

- Видит **только** задачи, где он указан как `executor`
- Может менять статус своих задач (выполнено / не выполнено)
- Не может создавать, редактировать или удалять задачи

### Смена статуса

Любой пользователь (начальник или подчинённый) может изменить статус задачи, **если он назначен исполнителем** (`task.executor == user`).

### Реализация

Роль проверяется через `User.groups` и пользовательский миксин:

| Миксин | Кто пропускает |
|---|---|
| `BossRequiredMixin` | Только начальников |

Кастомный шаблонный фильтр `has_group(user, group_name)` используется в шаблонах для условного отображения кнопок.

---

## Модель данных

### Task

| Поле | Тип | Описание |
|---|---|---|
| `id` | AutoField | Первичный ключ |
| `title` | `CharField(200)` | Название задачи |
| `description` | `TextField` (nullable) | Описание задачи |
| `priority` | `CharField` | `high` / `medium` / `low` (High / Средний / Низкий) |
| `status` | `BooleanField` | `False` = в работе, `True` = выполнено |
| `created_at` | `DateTimeField` | Дата создания (автоматически) |
| `updated_at` | `DateTimeField` | Дата последнего обновления (auto_now) |
| `author` | `ForeignKey → User` (CASCADE) | Начальник, создавший задачу |
| `executor` | `ForeignKey → User` (SET_NULL) | Подчинённый, исполняющий задачу |

### Порядок сортировки

1. Сначала невыполненные задачи (`status = False`)
2. Затем по приоритету: **High** → **Medium** → **Low**
3. Внутри одинакового приоритета — по дате: **новые сначала**

### Группы

Группы создаются в процессе эксплуатации. При создании пользователя через форму его автоматически добавляют в соответствующую группу (`"Начальник"` или `"Подчинённый"`).

---

## Маршруты (URLs)

### Корневые маршруты (`taskmanager/urls.py`)

| URL | View | Имя |
|---|---|---|
| `/admin/` | Django Admin | `admin:index` |
| `/accounts/login/` | `LoginView` | `login` |
| `/accounts/logout/` | `LogoutView` | `logout` |
| `/` | `include('core.urls')` | — |

### Маршруты приложения `core`

| URL | View | Имя | Роль |
|---|---|---|---|
| `/` | `TaskListView` | `task-list` | Все авторизованные |
| `/<int:pk>/` | `TaskDetailView` | `task-detail` | Все авторизованные |
| `create/` | `TaskCreateView` | `task-create` | Начальник |
| `edit/<int:pk>/` | `TaskUpdateView` | `task-update` | Начальник |
| `delete/<int:pk>/` | `TaskDeleteView` | `task-delete` | Начальник |
| `status/<int:pk>/` | `TaskStatusUpdateView` | `task-status` | Исполнитель (начальник или подчинённый) |
| `users/boss/create/` | `BossUserCreateView` | `boss-user-create` | Начальник |
| `users/edit/<int:pk>/` | `BossUserUpdateView` | `boss-user-update` | Начальник |
| `users/employee/create/` | `EmployeeUserCreateView` | `employee-user-create` | Начальник |

---

## Конфигурация

### `settings.py` — ключевые параметры

| Параметр | Значение |
|---|---|
| `TIME_ZONE` | `Europe/Moscow` |
| `LANGUAGE_CODE` | `ru` |
| `DATABASE` | SQLite (`db.sqlite3`) |
| `STATIC_URL` | `/static/` |
| `LOGIN_REDIRECT_URL` | `/` |
| `LOGOUT_REDIRECT_URL` | `/` |
| `CRISPY_ALLOWED_TEMPLATE_PACKS` | `bootstrap5` |
| `CRISPY_TEMPLATE_PACK` | `bootstrap5` |
| `AUTH_PASSWORD_MIN_LENGTH` | `8` символов |

### Переменные окружения

| Переменная | Обязательно | По умолчанию | Описание |
|---|---|---|---|
| `DJANGO_SECRET_KEY` | Да | — | Ключ секретности Django |
| `DJANGO_DEBUG` | Нет | `True` | Режим отладки |
| `DJANGO_ALLOWED_HOSTS` | Нет | `localhost` | Разрешённые хосты |

### Безопасность (Production)

При `DEBUG=False` включаются:

- `SECURE_SSL_REDIRECT = True`
- `SESSION_COOKIE_SECURE = True`
- `CSRF_COOKIE_SECURE = True`
- `SECURE_BROWSER_XSS_FILTER = True`
- `X_CONTENT_TYPE_OPTIONS = 'nosniff'`

---

## Шаблоны и статика

### Структура шаблонов

```
core/templates/core/
├── base.html           # Базовый лейаут: хедер, навигация, flash-messages
├── login.html          # Форма входа (Django LoginView)
├── task_list.html      # Карточная сетка задач
├── task_detail.html    # Полная информация о задаче
├── task_form.html      # Форма создания и редактирования задачи
├── task_confirm_delete.html
└── user_create_form.html  # Единая форма для создания/редактирования пользователей
```

### Статические файлы

```
core/static/css/
├── base.css            # Глобальные стили, хедер, уведомления
├── task_list.css       # Стили карточной сетки и таблицы пользователей
├── task_detail.css     # Стили страницы задачи
├── task_form.css       # Стили форм
├── user_form.css       # Стили форм пользователей
└── login.css           # Стили страницы входа
```

### Кастомный тег шаблона

`core/templatetags/roles.py` — региструет фильтр `has_group`:

```html
{% load roles %}

{% if user|has_group:"Начальник" %}
    <a href="{% url 'task-create' %}">Создать задачу</a>
{% endif %}
```

---

## Технические детали

### Миграции

| # | Файл | Описание |
|---|---|---|
| 1 | `0001_initial` | Создание модели `Task` (без поля `executor`) |
| 2 | `0002_alter_task_options` | Сортировка: `-created_at, priority` |
| 3 | `0003_alter_task_options` | Сортировка по приоритету (Case/When), затем status, затем `-created_at` |
| 4 | `0004_alter_task_options_task_executor` | Добавление поля `executor`, финализация сортировки |

### Формы

| Форма | Класс | Использование |
|---|---|---|
| `TaskForm` | `ModelForm` | CRUD задач (поля: title, description, priority, status, executor) |
| `StatusForm` | `Form` | Поле `status` (bool) для смены статуса исполнителем |
| `BaseUserCreateForm` | `ModelForm` (базовый) | Базовая форма создания пользователя с назначением группы |
| `BossUserCreateForm` | `BaseUserCreateForm` | Создание/редактирование начальника |
| `EmployeeUserCreateForm` | `BaseUserCreateForm` | Создание подчинённого |

### View-классы

| View | Тип | GET | POST | Роль |
|---|---|---|---|---|
| `TaskListView` | `ListView` | Список задач | — | Все |
| `TaskDetailView` | `DetailView` | Детали задачи | — | Все |
| `TaskCreateView` | `CreateView` | Пустая форма | Создание | Начальник |
| `TaskUpdateView` | `UpdateView` | Форма с данными | Обновление | Начальник |
| `TaskDeleteView` | `DeleteView` | Подтверждение | Удаление | Начальник |
| `TaskStatusUpdateView` | `View` | Смена статуса | Смена статуса | Исполнитель (начальник или подчинённый) |
| `BossUserCreateView` | `CreateView` | Форма создания | Создание | Начальник |
| `BossUserUpdateView` | `UpdateView` | Форма редактирования | Обновление | Начальник |
| `EmployeeUserCreateView` | `CreateView` | Форма создания | Создание | Начальник |

###bekend-замечания

Все замечания устранены:
- ✅ **34+ автоматических теста** покрывают модели, формы, представления и права доступа.
- ✅ Избыточный импорт в `models.py` вынесен на уровень модуля.
- ✅ Артефакт `task_list 3.html` удалён.
- ✅ Общая логика форм вынесена в базовый класс `BaseUserCreateForm`.
- ✅ `task_update.html` объединён с `task_form.html`.
- ✅ Дублирующие формы пользователей объединены в `user_create_form.html`.
- ✅ `EmployeeRequiredMixin` удалён (не использовался).
- ✅ `MAILERS` заменён на `EMAIL_BACKEND`.
- ✅ `LANGUAGE_CODE` изменён на `ru`.
- ✅ Минимальная длина пароля унифицирована: **8 символов** (settings, forms, widget).
- ✅ `task_list.html` использует `get_full_name` вместо `username`.

---

## Структура базы данных

```
User ──< Task (author)
          │
          └──> User (executor)  (SET_NULL при удалении)

Group ──< User (многие-ко-многим)
```

---

## Лицензия

Информация отсутствует.

---

## Деплой в продакшен

### Вариант 1: Docker (Рекомендуется)

#### Сборка и запуск через Docker Compose

```bash
# 1. Скопируйте и настройте переменные окружения
cp .env.example .env

# 2. Отредактируйте .env, указав правильные значения:
#    - DJANGO_SECRET_KEY (сгенерируйте новый секретный ключ)
#    - DJANGO_DEBUG=False
#    - DJANGO_ALLOWED_HOSTS (ваш домен)
#    - Email настройки (при необходимости)

# 3. Соберите и запустите контейнеры
docker-compose up -d --build

# 4. Примените миграции в контейнере
docker-compose exec web python manage.py migrate

# 5. Создайте суперпользователя
docker-compose exec web python manage.py createsuperuser
```

#### Проверка здоровья приложения

```bash
# Health check endpoint
curl http://localhost:8000/health/
```

#### Логи

```bash
# Просмотр логов
docker-compose logs -f web

# Остановка
docker-compose down
```

---

### Вариант 2: Прямой деплой на сервер

#### 1. Подготовка сервера

```bash
# Установка Python и зависимостей
sudo apt update
sudo apt install python3-pip python3-venv postgresql nginx

# Клонирование репозитория
git clone <repository-url>
cd taskmanager
```

#### 2. Настройка виртуального окружения

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 3. Настройка переменных окружения

```bash
# Создайте .env файл
cp .env.example .env
# Отредактируйте .env с production-значениями
```

#### 4. Миграции и статика

```bash
# Примените миграции
python manage.py migrate

# Соберите статические файлы
python manage.py collectstatic --noinput

# Проверьте конфигурацию
python manage.py check --deploy
```

#### 5. Запуск через Gunicorn

```bash
# Создайте systemd сервис
sudo nano /etc/systemd/system/taskmanager.service
```

Содержимое файла сервиса:

```ini
[Unit]
Description=TaskManager AI Django Application
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/taskmanager
ExecStart=/path/to/taskmanager/venv/bin/gunicorn \
    --access-logfile - \
    --workers 4 \
    --timeout 120 \
    --bind unix:/path/to/taskmanager/taskmanager.sock \
    taskmanager.wsgi:application

Restart=on-failure

[Install]
WantedBy=multi-user.target
```

```bash
# Запустите сервис
sudo systemctl start taskmanager
sudo systemctl enable taskmanager
sudo systemctl status taskmanager
```

#### 6. Настройка Nginx

```bash
sudo nano /etc/nginx/sites-available/taskmanager
```

Содержимое конфигурации Nginx:

```nginx
server {
    listen 80;
    server_name example.com www.example.com;

    location / {
        proxy_pass http://unix:/path/to/taskmanager/taskmanager.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /path/to/taskmanager/staticfiles/;
    }

    location /health/ {
        access_log off;
        proxy_pass http://unix:/path/to/taskmanager/taskmanager.sock;
    }
}
```

```bash
# Активируйте сайт
sudo ln -s /etc/nginx/sites-available/taskmanager /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

### Вариант 3: Heroku

#### 1. Подготовка

```bash
# Установите Heroku CLI и войдите
heroku login

# Создайте новое приложение
heroku create your-app-name

# Добавьте PostgreSQL
heroku addons:create heroku-postgresql:hobby-dev

# Настройте переменные окружения
heroku config:set DJANGO_SECRET_KEY=$(openssl rand -base64 50)
heroku config:set DJANGO_DEBUG=False
heroku config:set DJANGO_ALLOWED_HOSTS=your-app-name.herokuapp.com
```

#### 2. Деплой

```bash
# Добавьте remote
git remote add heroku https://git.heroku.com/your-app-name.git

# Деплой
git push heroku main

# Примените миграции
heroku run python manage.py migrate

# Создайте суперпользователя
heroku run python manage.py createsuperuser

# Откройте приложение
heroku open
```

---

### Вариант 4: Platform.sh / Railway / Render

Все платформы поддерживают Docker. Используйте `Dockerfile` и `docker-compose.yml` для деплоя.

#### Основные требования:

1. Установите `DJANGO_DEBUG=False`
2. Сгенерируйте новый `DJANGO_SECRET_KEY`
3. Настройте `DJANGO_ALLOWED_HOSTS` с вашим доменом
4. Настройте email backend для отправки уведомлений
5. Настройте базу данных (PostgreSQL recommended)

---

### Production Checklist

- [ ] `DJANGO_DEBUG=False`
- [ ] Сильный `DJANGO_SECRET_KEY` (минимум 50 символов)
- [ ] `DJANGO_ALLOWED_HOSTS` настроен с правильными доменами
- [ ] Статика собрана: `python manage.py collectstatic`
- [ ] Миграции применены: `python manage.py migrate`
- [ ] Email backend настроен для production
- [ ] HTTPS включен (через Nginx/Let's Encrypt или прокси)
- [ ] База данных перенесена на PostgreSQL (опционально)
- [ ] Резервное копирование базы данных настроено
- [ ] Логи доступны и мониторятся
- [ ] Health check endpoint работает: `/health/`
