from typing import ClassVar

from django.contrib.auth.models import User
from django.db import models


class TaskList(models.Model):
    objects: ClassVar[models.Manager["TaskList"]] = models.Manager()
    name = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="task_lists")
    description = models.TextField(blank=True, null=True)
    color = models.CharField(max_length=7, default="#FFFFFF")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return str(self.name)


class Task(models.Model):
    class Priority(models.TextChoices):
        LOW = "low", "Baixa"
        MEDIUM = "medium", "Média"
        HIGH = "high", "Alta"

    class Status(models.TextChoices):
        PENDING = "pending", "Pendente"
        IN_PROGRESS = "in_progress", "Em andamento"
        DONE = "done", "Concluída"

    objects: ClassVar[models.Manager["Task"]] = models.Manager()
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="tasks", null=True, blank=True
    )
    task_list = models.ForeignKey(
        TaskList, on_delete=models.CASCADE, related_name="tasks"
    )  # Permite acessar lista.tasks diretamente.
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    priority = models.CharField(
        max_length=10, choices=Priority.choices, default=Priority.MEDIUM
    )
    status = models.CharField(
        max_length=15, choices=Status.choices, default=Status.PENDING
    )
    due_date = models.DateField(null=True, blank=True)
    planned_date = models.DateField(
        null=True, blank=True
    )  # Data planejada para execução, diferente da data de vencimento.
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(
        auto_now=True
    )  # Atualiza automaticamente a cada save().

    @property
    def done(self) -> bool:
        return self.status == self.Status.DONE

    def __str__(self) -> str:
        return str(self.title)


class SubTask(models.Model):
    objects: ClassVar[models.Manager["SubTask"]] = models.Manager()
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="subtasks")
    title = models.CharField(max_length=255)
    done = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return str(self.title)
