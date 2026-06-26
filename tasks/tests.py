import datetime

from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from .models import SubTask, Task, TaskList


class TaskListViewSetTests(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            "owner", "owner@example.com", "sE7!kM2@nP9#xQ1"
        )
        self.other_user = User.objects.create_user(
            "other", "other@example.com", "sE7!kM2@nP9#xQ1"
        )
        self.task_list = TaskList.objects.create(user=self.user, name="Compras")
        self.other_list = TaskList.objects.create(
            user=self.other_user, name="Trabalho"
        )

    def test_unauthenticated_request_is_rejected(self) -> None:
        response = self.client.get(reverse("tasks:tasklist-list"))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_owner_sees_only_own_task_lists(self) -> None:
        self.client.force_authenticate(self.user)

        response = self.client.get(reverse("tasks:tasklist-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [item["name"] for item in response.data]
        self.assertEqual(names, ["Compras"])

    def test_user_can_create_task_list(self) -> None:
        self.client.force_authenticate(self.user)

        response = self.client.post(
            reverse("tasks:tasklist-list"),
            {"name": "Viagem", "description": "Mala", "color": "#00FF00"},
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        task_list = TaskList.objects.get(name="Viagem")
        self.assertEqual(task_list.user, self.user)

    def test_user_cannot_spoof_owner_on_create(self) -> None:
        self.client.force_authenticate(self.user)

        response = self.client.post(
            reverse("tasks:tasklist-list"),
            {"name": "Viagem", "user": self.other_user.pk},
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        task_list = TaskList.objects.get(name="Viagem")
        self.assertEqual(task_list.user, self.user)

    def test_owner_can_update_own_task_list(self) -> None:
        self.client.force_authenticate(self.user)

        response = self.client.patch(
            reverse("tasks:tasklist-detail", kwargs={"pk": self.task_list.pk}),
            {"name": "Mercado"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.task_list.refresh_from_db()
        self.assertEqual(self.task_list.name, "Mercado")

    def test_owner_can_delete_own_task_list(self) -> None:
        self.client.force_authenticate(self.user)

        response = self.client.delete(
            reverse("tasks:tasklist-detail", kwargs={"pk": self.task_list.pk})
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(TaskList.objects.filter(pk=self.task_list.pk).exists())

    def test_user_cannot_access_other_users_task_list(self) -> None:
        self.client.force_authenticate(self.user)

        response = self.client.get(
            reverse("tasks:tasklist-detail", kwargs={"pk": self.other_list.pk})
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_cannot_delete_other_users_task_list(self) -> None:
        self.client.force_authenticate(self.user)

        response = self.client.delete(
            reverse("tasks:tasklist-detail", kwargs={"pk": self.other_list.pk})
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(TaskList.objects.filter(pk=self.other_list.pk).exists())


class TaskViewSetTests(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            "owner", "owner@example.com", "sE7!kM2@nP9#xQ1"
        )
        self.other_user = User.objects.create_user(
            "other", "other@example.com", "sE7!kM2@nP9#xQ1"
        )
        self.task_list = TaskList.objects.create(user=self.user, name="Compras")
        self.other_list = TaskList.objects.create(
            user=self.other_user, name="Trabalho"
        )
        self.task = Task.objects.create(
            owner=self.user, task_list=self.task_list, title="Leite"
        )
        self.other_task = Task.objects.create(
            owner=self.other_user, task_list=self.other_list, title="Privada"
        )

    def test_unauthenticated_request_is_rejected(self) -> None:
        response = self.client.get(reverse("tasks:task-list"))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_sees_only_tasks_from_own_lists(self) -> None:
        self.client.force_authenticate(self.user)

        response = self.client.get(reverse("tasks:task-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        titles = [item["title"] for item in response.data]
        self.assertEqual(titles, ["Leite"])

    def test_user_can_create_task_within_own_list(self) -> None:
        self.client.force_authenticate(self.user)

        response = self.client.post(
            reverse("tasks:task-list"),
            {
                "task_list": self.task_list.pk,
                "title": "Pão",
                "priority": Task.Priority.HIGH,
                "status": Task.Status.PENDING,
                "due_date": "2026-04-30",
                "planned_date": "2026-04-21",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        task = Task.objects.get(title="Pão")
        self.assertEqual(task.owner, self.user)
        self.assertEqual(task.task_list, self.task_list)

    def test_user_cannot_spoof_owner_on_create(self) -> None:
        self.client.force_authenticate(self.user)

        response = self.client.post(
            reverse("tasks:task-list"),
            {
                "task_list": self.task_list.pk,
                "title": "Pão",
                "owner": self.other_user.pk,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        task = Task.objects.get(title="Pão")
        self.assertEqual(task.owner, self.user)

    def test_user_cannot_create_task_in_other_users_list(self) -> None:
        self.client.force_authenticate(self.user)

        response = self.client.post(
            reverse("tasks:task-list"),
            {"task_list": self.other_list.pk, "title": "Invadir"},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Task.objects.filter(title="Invadir").exists())

    def test_user_can_mark_task_done_via_update(self) -> None:
        self.client.force_authenticate(self.user)

        response = self.client.patch(
            reverse("tasks:task-detail", kwargs={"pk": self.task.pk}),
            {"status": Task.Status.DONE},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, Task.Status.DONE)
        self.assertTrue(self.task.done)
        self.assertTrue(response.data["done"])

    def test_owner_can_delete_own_task(self) -> None:
        self.client.force_authenticate(self.user)

        response = self.client.delete(
            reverse("tasks:task-detail", kwargs={"pk": self.task.pk})
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Task.objects.filter(pk=self.task.pk).exists())

    def test_user_cannot_access_other_users_task(self) -> None:
        self.client.force_authenticate(self.user)

        response = self.client.get(
            reverse("tasks:task-detail", kwargs={"pk": self.other_task.pk})
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_cannot_update_other_users_task(self) -> None:
        self.client.force_authenticate(self.user)

        response = self.client.patch(
            reverse("tasks:task-detail", kwargs={"pk": self.other_task.pk}),
            {"title": "Hackeada"},
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.other_task.refresh_from_db()
        self.assertEqual(self.other_task.title, "Privada")

    def test_toggle_marks_pending_task_as_done(self) -> None:
        self.client.force_authenticate(self.user)

        response = self.client.post(
            reverse("tasks:task-toggle", kwargs={"pk": self.task.pk})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, Task.Status.DONE)
        self.assertTrue(response.data["done"])

    def test_toggle_marks_done_task_as_pending(self) -> None:
        self.task.status = Task.Status.DONE
        self.task.save(update_fields=["status"])
        self.client.force_authenticate(self.user)

        response = self.client.post(
            reverse("tasks:task-toggle", kwargs={"pk": self.task.pk})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, Task.Status.PENDING)

    def test_user_cannot_toggle_other_users_task(self) -> None:
        self.client.force_authenticate(self.user)

        response = self.client.post(
            reverse("tasks:task-toggle", kwargs={"pk": self.other_task.pk})
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TaskFilterActionsTests(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            "owner", "owner@example.com", "sE7!kM2@nP9#xQ1"
        )
        self.task_list = TaskList.objects.create(user=self.user, name="Compras")
        self.today = timezone.localdate()

        self.today_task = Task.objects.create(
            owner=self.user,
            task_list=self.task_list,
            title="Hoje",
            planned_date=self.today,
        )
        self.late_task = Task.objects.create(
            owner=self.user,
            task_list=self.task_list,
            title="Atrasada",
            due_date=self.today - datetime.timedelta(days=3),
        )
        self.done_task = Task.objects.create(
            owner=self.user,
            task_list=self.task_list,
            title="Concluída",
            status=Task.Status.DONE,
        )
        self.future_task = Task.objects.create(
            owner=self.user,
            task_list=self.task_list,
            title="Futura",
            due_date=self.today + datetime.timedelta(days=10),
        )

    def test_today_returns_tasks_planned_or_due_today(self) -> None:
        self.client.force_authenticate(self.user)

        response = self.client.get(reverse("tasks:task-today"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        titles = {item["title"] for item in response.data}
        self.assertEqual(titles, {"Hoje"})

    def test_late_returns_overdue_pending_tasks(self) -> None:
        self.client.force_authenticate(self.user)

        response = self.client.get(reverse("tasks:task-late"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        titles = {item["title"] for item in response.data}
        self.assertEqual(titles, {"Atrasada"})

    def test_completed_returns_done_tasks(self) -> None:
        self.client.force_authenticate(self.user)

        response = self.client.get(reverse("tasks:task-completed"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        titles = {item["title"] for item in response.data}
        self.assertEqual(titles, {"Concluída"})

    def test_ordering_query_param_orders_by_priority(self) -> None:
        self.client.force_authenticate(self.user)

        response = self.client.get(reverse("tasks:task-list"), {"ordering": "priority"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TaskListPendingCountTests(APITestCase):
    def test_list_serializer_includes_pending_count(self) -> None:
        user = User.objects.create_user(
            "owner", "owner@example.com", "sE7!kM2@nP9#xQ1"
        )
        task_list = TaskList.objects.create(user=user, name="Compras")
        Task.objects.create(owner=user, task_list=task_list, title="Leite")
        Task.objects.create(
            owner=user,
            task_list=task_list,
            title="Pão",
            status=Task.Status.DONE,
        )
        self.client.force_authenticate(user)

        response = self.client.get(reverse("tasks:tasklist-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["pending_count"], 1)


class SubTaskViewSetTests(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            "owner", "owner@example.com", "sE7!kM2@nP9#xQ1"
        )
        self.other_user = User.objects.create_user(
            "other", "other@example.com", "sE7!kM2@nP9#xQ1"
        )
        self.task_list = TaskList.objects.create(user=self.user, name="Compras")
        self.other_list = TaskList.objects.create(
            user=self.other_user, name="Trabalho"
        )
        self.task = Task.objects.create(
            owner=self.user, task_list=self.task_list, title="Leite"
        )
        self.other_task = Task.objects.create(
            owner=self.other_user, task_list=self.other_list, title="Privada"
        )
        self.subtask = SubTask.objects.create(task=self.task, title="Comprar leite")
        self.other_subtask = SubTask.objects.create(
            task=self.other_task, title="Tarefa privada"
        )

    def test_unauthenticated_request_is_rejected(self) -> None:
        response = self.client.get(reverse("tasks:subtask-list"))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_sees_only_subtasks_from_own_tasks(self) -> None:
        self.client.force_authenticate(self.user)

        response = self.client.get(reverse("tasks:subtask-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        titles = [item["title"] for item in response.data]
        self.assertEqual(titles, ["Comprar leite"])

    def test_user_can_create_subtask_for_own_task(self) -> None:
        self.client.force_authenticate(self.user)

        response = self.client.post(
            reverse("tasks:subtask-list"),
            {"task": self.task.pk, "title": "Levar sacola"},
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            SubTask.objects.filter(task=self.task, title="Levar sacola").exists()
        )

    def test_user_cannot_create_subtask_for_other_users_task(self) -> None:
        self.client.force_authenticate(self.user)

        response = self.client.post(
            reverse("tasks:subtask-list"),
            {"task": self.other_task.pk, "title": "Invadir"},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(SubTask.objects.filter(title="Invadir").exists())

    def test_user_can_toggle_subtask(self) -> None:
        self.client.force_authenticate(self.user)

        response = self.client.post(
            reverse("tasks:subtask-toggle", kwargs={"pk": self.subtask.pk})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.subtask.refresh_from_db()
        self.assertTrue(self.subtask.done)
        self.assertTrue(response.data["done"])

    def test_user_cannot_access_other_users_subtask(self) -> None:
        self.client.force_authenticate(self.user)

        response = self.client.get(
            reverse("tasks:subtask-detail", kwargs={"pk": self.other_subtask.pk})
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class DashboardViewsTests(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            "owner", "owner@example.com", "sE7!kM2@nP9#xQ1"
        )
        self.other_user = User.objects.create_user(
            "other", "other@example.com", "sE7!kM2@nP9#xQ1"
        )
        self.task_list = TaskList.objects.create(user=self.user, name="Compras")
        self.other_list = TaskList.objects.create(
            user=self.other_user, name="Trabalho"
        )
        self.today = timezone.localdate()

        Task.objects.create(
            owner=self.user,
            task_list=self.task_list,
            title="Hoje",
            planned_date=self.today,
        )
        Task.objects.create(
            owner=self.user,
            task_list=self.task_list,
            title="Atrasada",
            due_date=self.today - datetime.timedelta(days=2),
        )
        Task.objects.create(
            owner=self.user,
            task_list=self.task_list,
            title="Alta prioridade",
            priority=Task.Priority.HIGH,
            due_date=self.today + datetime.timedelta(days=3),
        )
        Task.objects.create(
            owner=self.user,
            task_list=self.task_list,
            title="Concluída",
            status=Task.Status.DONE,
        )
        # Tarefa de outro usuário não deve aparecer em nenhum dos painéis.
        Task.objects.create(
            owner=self.other_user, task_list=self.other_list, title="Privada"
        )

    def test_unauthenticated_request_is_rejected(self) -> None:
        response = self.client.get(reverse("tasks:dashboard-summary"))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_summary_returns_expected_counts(self) -> None:
        self.client.force_authenticate(self.user)

        response = self.client.get(reverse("tasks:dashboard-summary"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["pending"], 3)
        self.assertEqual(response.data["overdue"], 1)
        self.assertEqual(response.data["today"], 1)
        self.assertEqual(response.data["completed_week"], 1)

    def test_upcoming_returns_overdue_near_due_and_high_priority_tasks(self) -> None:
        self.client.force_authenticate(self.user)

        response = self.client.get(reverse("tasks:dashboard-upcoming"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        titles = {item["title"] for item in response.data}
        self.assertEqual(titles, {"Atrasada", "Alta prioridade"})
