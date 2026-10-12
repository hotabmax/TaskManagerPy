from django.test import TestCase, RequestFactory, Client
from django.contrib.auth.models import User, Group
from django.contrib.messages import get_messages
from django.urls import reverse
import uuid

from .models import Task
from .forms import TaskForm, StatusForm, BaseUserCreateForm, BossUserCreateForm, EmployeeUserCreateForm
from .views import TaskListView, TaskDetailView, TaskCreateView, TaskUpdateView


# --- Тесты моделей ---

class TaskModelTest(TestCase):
    def setUp(self):
        self.author = User.objects.create_user(
            username='boss_user',
            email='boss@test.com',
            password='testpass123'
        )
        self.executor = User.objects.create_user(
            username='emp_user',
            email='emp@test.com',
            password='testpass123'
        )
        self.boss_group, _ = Group.objects.get_or_create(name='Начальник')
        self.author.groups.add(self.boss_group)

    def test_create_task(self):
        """Создание задачи корректно"""
        task = Task.objects.create(
            title='Тестовая задача',
            description='Описание задачи',
            priority='High',
            author=self.author,
            executor=self.executor
        )
        self.assertEqual(task.title, 'Тестовая задача')
        self.assertEqual(task.description, 'Описание задачи')
        self.assertEqual(task.priority, 'High')
        self.assertEqual(task.author, self.author)
        self.assertEqual(task.executor, self.executor)
        self.assertFalse(task.status)
        self.assertIsNotNone(task.created_at)
        self.assertIsNotNone(task.updated_at)

    def test_task_str(self):
        """Строковое представление задачи"""
        task = Task.objects.create(
            title='Test Title',
            author=self.author
        )
        self.assertEqual(str(task), 'Test Title')

    def test_task_default_priority(self):
        """Приоритет по умолчанию — Medium"""
        task = Task.objects.create(
            title='Default Priority',
            author=self.author
        )
        self.assertEqual(task.priority, 'Medium')

    def test_task_status_default(self):
        """Статус по умолчанию — False (не готово)"""
        task = Task.objects.create(
            title='Not Done',
            author=self.author
        )
        self.assertFalse(task.status)

    def test_task_delete_cascade(self):
        """Удаление автора удаляет задачу (CASCADE)"""
        task = Task.objects.create(
            title='Orphan Task',
            author=self.author
        )
        self.author.delete()
        self.assertFalse(Task.objects.filter(pk=task.pk).exists())

    def test_task_set_null_executor(self):
        """Удаление исполнителя устанавливает executor=None"""
        task = Task.objects.create(
            title='Task with executor',
            author=self.author,
            executor=self.executor
        )
        self.executor.delete()
        task.refresh_from_db()
        self.assertIsNone(task.executor)

    def test_task_ordering(self):
        """Задачи сортируются: сначала неготовые, затем по приоритету, затем по дате"""
        Task.objects.create(title='Low Priority', priority='Low', author=self.author)
        Task.objects.create(title='Done Task', status=True, author=self.author)
        Task.objects.create(title='High Priority', priority='High', author=self.author)
        
        tasks = list(Task.objects.all())
        # High Priority должен быть первым (не готовый + высокий приоритет)
        self.assertEqual(tasks[0].title, 'High Priority')


# --- Тесты форм ---

class TaskFormTest(TestCase):
    def setUp(self):
        self.author = User.objects.create_user(
            username='boss_user',
            password='testpass123'
        )

    def test_task_form_valid(self):
        """Валидная форма задачи проходит валидацию"""
        data = {
            'title': 'New Task',
            'description': 'Description here',
            'priority': 'High',
            'executor': ''
        }
        form = TaskForm(data=data)
        self.assertTrue(form.is_valid())

    def test_task_form_invalid_empty_title(self):
        """Форма не проходит валидацию без названия"""
        data = {
            'title': '',
            'description': 'Description',
            'priority': 'Medium',
            'executor': ''
        }
        form = TaskForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)

    def test_status_form_valid(self):
        """Форма изменения статуса валидна"""
        author = User.objects.create_user(username='test_user', password='testpass123')
        task = Task.objects.create(
            title='Task',
            author=author,
            status=False
        )
        form = StatusForm(data={'status': True}, instance=task)
        self.assertTrue(form.is_valid())


class UserFormTest(TestCase):
    def setUp(self):
        self.boss_group, _ = Group.objects.get_or_create(name='Начальник')
        self.emp_group, _ = Group.objects.get_or_create(name='Подчиненный')

    def test_base_form_role_name(self):
        """Базовая форма имеет role_name"""
        form = BaseUserCreateForm()
        self.assertEqual(form.role_name, 'Роль')

    def test_boss_form_role_name(self):
        """Форма начальника назначает группу 'Начальник'"""
        form = BossUserCreateForm()
        self.assertEqual(form.role_name, 'Начальник')

    def test_employee_form_role_name(self):
        """Форма подчиненного назначает группу 'Подчиненный'"""
        form = EmployeeUserCreateForm()
        self.assertEqual(form.role_name, 'Подчиненный')

    def test_user_form_password_mismatch(self):
        """Форма не проходит валидацию при несовпадении паролей"""
        data = {
            'username': f'test_{uuid.uuid4().hex[:8]}',
            'email': 'test@test.com',
            'first_name': 'Ivan',
            'last_name': 'Ivanov',
            'password': 'Password123!',
            'password_confirm': 'Different456!',
        }
        form = BossUserCreateForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)

    def test_boss_user_creation(self):
        """Создание пользователя с ролью начальника"""
        data = {
            'username': f'boss_{uuid.uuid4().hex[:8]}',
            'email': 'boss_new@test.com',
            'first_name': 'Petr',
            'last_name': 'Petrov',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
        }
        form = BossUserCreateForm(data=data)
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertEqual(user.email, 'boss_new@test.com')
        self.assertTrue(user.groups.filter(name='Начальник').exists())

    def test_employee_user_creation(self):
        """Создание пользователя с ролью подчиненного"""
        data = {
            'username': f'employee_{uuid.uuid4().hex[:8]}',
            'email': 'emp_new@test.com',
            'first_name': 'Ivan',
            'last_name': 'Sidorov',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
        }
        form = EmployeeUserCreateForm(data=data)
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertEqual(user.email, 'emp_new@test.com')
        self.assertTrue(user.groups.filter(name='Подчиненный').exists())


# --- Тесты представлений ---

class TaskListViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.author = User.objects.create_user(
            username='boss_user',
            password='testpass123'
        )
        self.executor = User.objects.create_user(
            username='emp_user',
            password='testpass123'
        )
        self.boss_group, _ = Group.objects.get_or_create(name='Начальник')
        self.emp_group, _ = Group.objects.get_or_create(name='Подчиненный')
        self.author.groups.add(self.boss_group)
        self.executor.groups.add(self.emp_group)
        self.task = Task.objects.create(
            title='Test Task',
            description='Test description',
            priority='High',
            author=self.author,
            executor=self.executor
        )

    def test_login_required(self):
        """Неавторизованный пользователь перенаправляется на логин"""
        response = self.client.get(reverse('task-list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_login_and_access(self):
        """Авторизованный пользователь видит список задач"""
        self.client.login(username='boss_user', password='testpass123')
        response = self.client.get(reverse('task-list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Task')

    def test_boss_sees_only_his_tasks(self):
        """Начальник видит только свои задачи или назначенные на него"""
        # Создаём задачу, где boss_user — автор
        boss_task = Task.objects.create(
            title='Boss Task',
            author=self.author
        )
        # Создаём задачу, где boss_user — исполнитель
        boss_executor_task = Task.objects.create(
            title='Boss as Executor',
            author=self.executor,
            executor=self.author
        )
        # Создаём задачу, где boss_user — ни автор, ни исполнитель
        other_task = Task.objects.create(
            title='Other Task',
            author=self.executor,
            executor=User.objects.create_user(
                username='other_emp',
                password='testpass123'
            )
        )
        
        self.client.login(username='boss_user', password='testpass123')
        response = self.client.get(reverse('task-list'))
        self.assertContains(response, 'Test Task')  # executor=self.author
        self.assertContains(response, 'Boss Task')  # author=self.author
        self.assertContains(response, 'Boss as Executor')  # executor=self.author
        self.assertNotContains(response, 'Other Task')  # не относится к boss_user

    def test_employee_sees_assigned_tasks(self):
        """Подчиненный видит только назначенные задачи"""
        other_task = Task.objects.create(
            title='Other Task',
            author=self.author,
            executor=User.objects.create_user(
                username='other_emp',
                password='testpass123'
            )
        )
        self.client.login(username='emp_user', password='testpass123')
        response = self.client.get(reverse('task-list'))
        self.assertContains(response, 'Test Task')
        self.assertNotContains(response, 'Other Task')


class TaskCreateViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.author = User.objects.create_user(
            username='boss_user',
            password='testpass123'
        )
        self.boss_group, _ = Group.objects.get_or_create(name='Начальник')
        self.author.groups.add(self.boss_group)

    def test_boss_can_create_task(self):
        """Начальник может создать задачу"""
        self.client.login(username='boss_user', password='testpass123')
        data = {
            'title': 'New Task From View',
            'description': 'Created via view test',
            'priority': 'Medium',
            'executor': ''
        }
        response = self.client.post(reverse('task-create'), data)
        self.assertEqual(Task.objects.filter(title='New Task From View').count(), 1)
        task = Task.objects.get(title='New Task From View')
        self.assertEqual(task.author, self.author)

    def test_unauthorized_cannot_create(self):
        """Неавторизованный пользователь не может создать задачу"""
        data = {
            'title': 'Hacker Task',
            'description': 'Hack attempt',
            'priority': 'Low',
            'executor': ''
        }
        response = self.client.post(reverse('task-create'), data)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Task.objects.filter(title='Hacker Task').exists())


class TaskUpdateViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.author = User.objects.create_user(
            username='boss_user',
            password='testpass123'
        )
        self.boss_group, _ = Group.objects.get_or_create(name='Начальник')
        self.author.groups.add(self.boss_group)
        self.task = Task.objects.create(
            title='Original Title',
            description='Original description',
            priority='Medium',
            author=self.author
        )

    def test_boss_can_update_task(self):
        """Начальник может редактировать свою задачу"""
        self.client.login(username='boss_user', password='testpass123')
        data = {
            'title': 'Updated Title',
            'description': 'Updated description',
            'priority': 'High',
            'executor': ''
        }
        response = self.client.post(
            reverse('task-update', kwargs={'pk': self.task.pk}),
            data
        )
        self.task.refresh_from_db()
        self.assertEqual(self.task.title, 'Updated Title')
        self.assertEqual(self.task.priority, 'High')


class TaskDetailViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.author = User.objects.create_user(
            username='boss_user',
            password='testpass123'
        )
        self.executor = User.objects.create_user(
            username='emp_user',
            password='testpass123'
        )
        self.boss_group, _ = Group.objects.get_or_create(name='Начальник')
        self.emp_group, _ = Group.objects.get_or_create(name='Подчиненный')
        self.author.groups.add(self.boss_group)
        self.executor.groups.add(self.emp_group)
        self.task = Task.objects.create(
            title='Shared Task',
            author=self.author,
            executor=self.executor
        )

    def test_author_can_see_task(self):
        """Автор видит свою задачу"""
        self.client.login(username='boss_user', password='testpass123')
        response = self.client.get(reverse('task-detail', kwargs={'pk': self.task.pk}))
        self.assertEqual(response.status_code, 200)

    def test_executor_can_see_task(self):
        """Исполнитель видит назначенную задачу"""
        self.client.login(username='emp_user', password='testpass123')
        response = self.client.get(reverse('task-detail', kwargs={'pk': self.task.pk}))
        self.assertEqual(response.status_code, 200)

    def test_boss_cannot_see_others_task(self):
        """Начальник не видит чужую задачу, если он не автор и не исполнитель"""
        other_task = Task.objects.create(
            title='Other Task',
            author=self.executor,
            executor=User.objects.create_user(
                username='other_emp',
                password='testpass123'
            )
        )
        self.client.login(username='boss_user', password='testpass123')
        response = self.client.get(reverse('task-detail', kwargs={'pk': other_task.pk}))
        self.assertEqual(response.status_code, 403)

    def test_boss_can_see_assigned_task(self):
        """Начальник видит задачу, где он назначен исполнителем"""
        boss_as_executor = Task.objects.create(
            title='Boss as Executor Task',
            author=self.executor,
            executor=self.author
        )
        self.client.login(username='boss_user', password='testpass123')
        response = self.client.get(reverse('task-detail', kwargs={'pk': boss_as_executor.pk}))
        self.assertEqual(response.status_code, 200)

    def test_other_employee_cannot_see_task(self):
        """Другой подчиненный не видит чужую задачу"""
        other_emp = User.objects.create_user(
            username='other_emp',
            password='testpass123'
        )
        other_emp.groups.add(self.emp_group)
        self.client.login(username='other_emp', password='testpass123')
        response = self.client.get(reverse('task-detail', kwargs={'pk': self.task.pk}))
        self.assertEqual(response.status_code, 403)


class UserFormViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.boss = User.objects.create_user(
            username='super_boss',
            password='testpass123'
        )
        self.boss_group, _ = Group.objects.get_or_create(name='Начальник')
        self.boss.groups.add(self.boss_group)

    def test_boss_can_create_user(self):
        """Начальник может создать нового пользователя"""
        self.client.login(username='super_boss', password='testpass123')
        data = {
            'username': f'new_user_{uuid.uuid4().hex[:8]}',
            'email': 'newuser@test.com',
            'first_name': 'Alex',
            'last_name': 'Alexandrov',
            'password': 'NewPass123!',
            'password_confirm': 'NewPass123!',
        }
        response = self.client.post(reverse('boss-user-create'), data)
        self.assertEqual(User.objects.filter(email='newuser@test.com').count(), 1)

    def test_unauthorized_cannot_access_user_creation(self):
        """Неавторизованный пользователь не может создать пользователя"""
        response = self.client.get(reverse('boss-user-create'))
        self.assertEqual(response.status_code, 302)
