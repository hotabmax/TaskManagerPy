# TaskManagerAI

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
| **Смена статуса** | Подчинённый может отметить задачу как выполненную / не выполненную. |
| **Фильтрация по ролям** | Подчинённый видит **только свои** задачи; начальник видит **все** задачи. |
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
│   │   ├── task_form.html        # Создание задачи
│   │   ├── task_update.html      # Редактирование задачи
│   │   ├── task_confirm_delete.html
│   │   ├── user_form.html        # Создание/редактирование начальника
│   │   └── employee_user_form.html
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

- Видит **все** задачи
- Создаёт / редактирует / удаляет задачи
- Назначает исполнителей
- Создаёт новые учётные записи (начальников и подчинённых)
- Доступ к админ-панели (`/admin/`)

### Подчинённый (`Group: "Подчинённый"`)

- Видит **только** задачи, где он указан как `executor`
- Может менять статус своих задач (выполнено / не выполнено)
- Не может создавать, редактировать или удалять задачи

### Реализация

Роль проверяется через `User.groups` и пользовательские миксины:

| Миксин | Кто пропускает |
|---|---|
| `BossRequiredMixin` | Только начальников |
| `EmployeeRequiredMixin` | Только подчинённых |

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
| `status/<int:pk>/` | `TaskStatusUpdateView` | `task-status` | Подчинённый |
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
| `MEDIA_URL` | `/media/` |
| `LOGIN_URL` | `login` |
| `LOGIN_REDIRECT_URL` | `task-list` |
| `LOGOUT_REDIRECT_URL` | `login` |
| `CRISPY_ALLOWED_TEMPLATE_PACKS` | `bootstrap5` |
| `CRISPY_TEMPLATE_PACK` | `bootstrap5` |

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
├── base.html           # Базовый лейаут: хедер, навигация, flash-messages, footer
├── login.html          # Форма входа (Django LoginView)
├── task_list.html      # Карточная сетка задач
├── task_detail.html    # Полная информация о задаче
├── task_form.html      # Форма создания задачи
├── task_update.html    # Форма редактирования задачи
├── task_confirm_delete.html
├── user_form.html      # Форма создания/редактирования начальника
└── employee_user_form.html
```

### Статические файлы

```
core/static/css/
├── base.css            # Глобальные стили, хедер, уведомления
├── task_list.css       # Стили карточной сетки
├── task_detail.css     # Стили страницы задачи
├── task_form.css       # Стили форм
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
| `StatusForm` | `Form` | Поле `status` (bool) для смены статуса подчинённым |
| `BossUserCreateForm` | `ModelForm` | Создание начальника (User + Group assignment) |
| `EmployeeUserCreateForm` | `ModelForm` | Создание подчинённого (User + Group assignment) |

### View-классы

| View | Тип | GET | POST | Роль |
|---|---|---|---|---|
| `TaskListView` | `ListView` | Список задач | — | Все |
| `TaskDetailView` | `DetailView` | Детали задачи | — | Все |
| `TaskCreateView` | `CreateView` | Пустая форма | Создание | Начальник |
| `TaskUpdateView` | `UpdateView` | Форма с данными | Обновление | Начальник |
| `TaskDeleteView` | `DeleteView` | Подтверждение | Удаление | Начальник |
| `TaskStatusUpdateView` | `UpdateView` | Форма статуса | Смена статуса | Подчинённый |
| `BossUserCreateView` | `CreateView` | Форма создания | Создание | Начальник |
| `BossUserUpdateView` | `UpdateView` | Форма редактирования | Обновление | Начальник |
| `EmployeeUserCreateView` | `CreateView` | Форма создания | Создание | Начальник |

###bekend-замечания

- **Автоматические тесты отсутствуют** (`core/tests.py` пустой).
- В `models.py` присутствует избыточный импорт `from django.db.models import Case, When, IntegerField` внутри тела `Meta` (строка 42).
- Файл `task_list 3.html` — вероятный артефакт разработки (дубликат).
- `BossUserCreateForm` переиспользуется и для начальника, и для подчинённого (логика различается).
- `task_update.html` — отдельный шаблон для `TaskUpdateView`, не разделяется с `task_form.html`.

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

## Сборка для production

```bash
# 1. Установить DEBUG=False в .env
# 2. Установить секретный ключ
# 3. Собрать статику
python manage.py collectstatic
# 4. Запустить через Gunicorn / uWSGI
gunicorn taskmanager.wsgi
```
