from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Task, TaskList


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
