import datetime

from django.db.models import Count, Q
from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import SubTask, Task, TaskList
from .serializers import (
    DashboardSummarySerializer,
    SubTaskSerializer,
    TaskListSerializer,
    TaskSerializer,
)


@extend_schema_view(
    list=extend_schema(
        summary="Lista as listas de tarefas.",
        description="Lista as listas de tarefas (TaskList) pertencentes ao usuário autenticado.",
        tags=["Listas"],
    ),
    create=extend_schema(
        summary="Cria uma lista de tarefas.",
        description="Cria uma nova lista de tarefas (TaskList) para o usuário autenticado.",
        tags=["Listas"],
    ),
    retrieve=extend_schema(
        summary="Detalha uma lista de tarefas.",
        description="Retorna os dados de uma lista de tarefas do usuário autenticado.",
        tags=["Listas"],
    ),
    update=extend_schema(
        summary="Atualiza uma lista de tarefas.",
        description="Atualiza integralmente uma lista de tarefas do usuário autenticado.",
        tags=["Listas"],
    ),
    partial_update=extend_schema(
        summary="Atualiza parcialmente uma lista de tarefas.",
        description="Atualiza parcialmente uma lista de tarefas do usuário autenticado.",
        tags=["Listas"],
    ),
    destroy=extend_schema(
        summary="Remove uma lista de tarefas.",
        description="Remove uma lista de tarefas do usuário autenticado.",
        tags=["Listas"],
    ),
)
class TaskListViewSet(viewsets.ModelViewSet):
    """CRUD de listas de tarefas (TaskList) pertencentes ao usuário autenticado."""

    serializer_class = TaskListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self): #get_queryset é um método que retorna o conjunto de dados (queryset) que será usado para as operações do viewset. Aqui, ele filtra as listas de tarefas para incluir apenas aquelas pertencentes ao usuário autenticado, garantindo que cada usuário só veja suas próprias listas.
        if getattr(self, "swagger_fake_view", False): #caso a view seja uma visualização fake do Swagger (gerada para documentação), retorna um queryset vazio para evitar erros de serialização.
            return TaskList.objects.none()
        return (
            TaskList.objects.filter(user=self.request.user)
            .annotate(
                pending_count=Count(
                    "tasks",
                    filter=Q(
                        tasks__status__in=[Task.Status.PENDING, Task.Status.IN_PROGRESS]
                    ),
                )
            )
            .order_by("name")
        )

    def perform_create(self, serializer):
        #perform_create é um método que é chamado quando uma nova instância do modelo está sendo criada, chamado após a validação do serializer. Aqui, ele garante que o campo 'user' da TaskList seja automaticamente definido como o usuário autenticado, evitando que o usuário possa manipular esse campo no payload da requisição.
        serializer.save(user=self.request.user)


@extend_schema_view(
    list=extend_schema(
        summary="Lista as tarefas.",
        description="Lista as tarefas do usuário autenticado, ordenadas por status, prazo e título.",
        tags=["Tarefas"],
    ),
    create=extend_schema(
        summary="Cria uma tarefa.",
        description="Cria uma nova tarefa vinculada a uma lista do usuário autenticado.",
        tags=["Tarefas"],
    ),
    retrieve=extend_schema(
        summary="Detalha uma tarefa.",
        description="Retorna os dados de uma tarefa do usuário autenticado.",
        tags=["Tarefas"],
    ),
    update=extend_schema(
        summary="Atualiza uma tarefa.",
        description="Atualiza integralmente uma tarefa do usuário autenticado.",
        tags=["Tarefas"],
    ),
    partial_update=extend_schema(
        summary="Atualiza parcialmente uma tarefa.",
        description="Atualiza parcialmente uma tarefa do usuário autenticado.",
        tags=["Tarefas"],
    ),
    destroy=extend_schema(
        summary="Remove uma tarefa.",
        description="Remove uma tarefa do usuário autenticado.",
        tags=["Tarefas"],
    ),
    toggle=extend_schema(
        summary="Alterna status da tarefa.",
        description="Alterna o status da tarefa entre concluída e pendente.",
        tags=["Tarefas"],
        request=None,
    ),
    today=extend_schema(
        summary="Tarefas de hoje.",
        description="Lista as tarefas planejadas ou com prazo (due_date) para hoje.",
        tags=["Tarefas"],
        responses=TaskSerializer(many=True),
    ),
    late=extend_schema(
        summary="Tarefas atrasadas.",
        description="Lista as tarefas pendentes com prazo (due_date) já vencido.",
        tags=["Tarefas"],
        responses=TaskSerializer(many=True),
    ),
    completed=extend_schema(
        summary="Tarefas concluídas.",
        description="Lista as tarefas concluídas do usuário autenticado.",
        tags=["Tarefas"],
        responses=TaskSerializer(many=True),
    ),
)
class TaskViewSet(viewsets.ModelViewSet):
    """CRUD de tarefas, restritas ao usuário autenticado."""

    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = [
        "priority",
        "status",
        "due_date",
        "planned_date",
        "title",
        "created_at",
    ]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Task.objects.none()
        return (
            Task.objects.filter(task_list__user=self.request.user)
            .select_related("task_list", "owner")
            .order_by("status", "due_date", "planned_date", "title")
        )

    def perform_create(self, serializer):
        # Owner não vem do payload para evitar manipulação.
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=["post"])
    def toggle(self, request, pk=None):
        """Alterna o status da tarefa entre concluída e pendente."""
        task = self.get_object()
        task.status = (
            Task.Status.PENDING if task.status == Task.Status.DONE else Task.Status.DONE
        )
        task.save(update_fields=["status", "updated_at"])
        serializer = self.get_serializer(task)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def today(self, request):
        """Tarefas planejadas ou com prazo para hoje."""
        today = timezone.localdate()
        queryset = self.filter_queryset(
            self.get_queryset().filter(Q(planned_date=today) | Q(due_date=today))
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def late(self, request):
        """Tarefas pendentes com prazo (due_date) já vencido."""
        today = timezone.localdate()
        queryset = self.filter_queryset(
            self.get_queryset().filter(
                due_date__lt=today,
                status__in=[Task.Status.PENDING, Task.Status.IN_PROGRESS],
            )
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def completed(self, request):
        """Tarefas concluídas do usuário autenticado."""
        queryset = self.filter_queryset(
            self.get_queryset().filter(status=Task.Status.DONE)
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(
        summary="Lista as subtarefas.",
        description="Lista as subtarefas vinculadas às tarefas do usuário autenticado.",
        tags=["Subtarefas"],
    ),
    create=extend_schema(
        summary="Cria uma subtarefa.",
        description="Cria uma nova subtarefa vinculada a uma tarefa do usuário autenticado.",
        tags=["Subtarefas"],
    ),
    retrieve=extend_schema(
        summary="Detalha uma subtarefa.",
        description="Retorna os dados de uma subtarefa do usuário autenticado.",
        tags=["Subtarefas"],
    ),
    update=extend_schema(
        summary="Atualiza uma subtarefa.",
        description="Atualiza integralmente uma subtarefa do usuário autenticado.",
        tags=["Subtarefas"],
    ),
    partial_update=extend_schema(
        summary="Atualiza parcialmente uma subtarefa.",
        description="Atualiza parcialmente uma subtarefa do usuário autenticado.",
        tags=["Subtarefas"],
    ),
    destroy=extend_schema(
        summary="Remove uma subtarefa.",
        description="Remove uma subtarefa do usuário autenticado.",
        tags=["Subtarefas"],
    ),
    toggle=extend_schema(
        summary="Alterna status da subtarefa.",
        description="Alterna a subtarefa entre feita e pendente.",
        tags=["Subtarefas"],
        request=None,
    ),
)
class SubTaskViewSet(viewsets.ModelViewSet):
    """CRUD de subtarefas, restritas às tarefas do usuário autenticado."""

    serializer_class = SubTaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return SubTask.objects.none()
        return (
            SubTask.objects.filter(task__task_list__user=self.request.user)
            .select_related("task")
            .order_by("task", "id")
        )

    @action(detail=True, methods=["post"])
    def toggle(self, request, pk=None):
        """Alterna a subtarefa entre feita e pendente."""
        subtask = self.get_object()
        subtask.done = not subtask.done
        subtask.save(update_fields=["done"])
        serializer = self.get_serializer(subtask)
        return Response(serializer.data)


class DashboardSummaryView(APIView):
    """Contagens agregadas para o dashboard: pendentes, vencidas, hoje e concluídas na semana."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Resumo do dashboard.",
        description="Contagens agregadas para o dashboard: pendentes, vencidas, hoje e concluídas na semana.",
        tags=["Dashboard"],
        responses=DashboardSummarySerializer,
    )
    def get(self, request):
        user = request.user
        today = timezone.localdate()
        week_start = today - datetime.timedelta(days=today.weekday())

        base_qs = Task.objects.filter(task_list__user=user)
        # Partimos do conjunto base de tasks pendentes para reaproveitar os mesmos filtros.
        pending_qs = base_qs.filter(
            status__in=[Task.Status.PENDING, Task.Status.IN_PROGRESS]
        )

        data = {
            "pending": pending_qs.count(),
            "overdue": pending_qs.filter(due_date__lt=today).count(),
            "today": pending_qs.filter(
                Q(planned_date=today) | Q(due_date=today)
            ).count(),
            "completed_week": base_qs.filter(
                status=Task.Status.DONE, updated_at__date__gte=week_start
            ).count(),
        }
        return Response(data)


class DashboardUpcomingView(APIView):
    """Tarefas vencidas, próximas do prazo e de alta prioridade para o dashboard."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Próximas tarefas do dashboard.",
        description="Tarefas vencidas, próximas do prazo (7 dias) e de alta prioridade para o dashboard.",
        tags=["Dashboard"],
        responses=TaskSerializer(many=True),
    )
    def get(self, request):
        user = request.user
        today = timezone.localdate()

        base_qs = Task.objects.filter(task_list__user=user).select_related(
            "task_list", "owner"
        )
        pending_qs = base_qs.filter(
            status__in=[Task.Status.PENDING, Task.Status.IN_PROGRESS]
        )

        overdue = pending_qs.filter(due_date__lt=today).order_by("due_date")
        near_due = pending_qs.filter(
            due_date__gte=today, due_date__lte=today + datetime.timedelta(days=7)
        ).order_by("due_date")
        high_priority = pending_qs.filter(priority=Task.Priority.HIGH).order_by(
            "due_date"
        )

        seen_ids: set[int] = set()
        upcoming: list[Task] = []
        # As três listas podem se sobrepor; deduplicamos antes de limitar o painel.
        for task in list(overdue) + list(near_due) + list(high_priority):
            if task.pk not in seen_ids:
                seen_ids.add(task.pk)
                upcoming.append(task)

        serializer = TaskSerializer(
            upcoming[:10], many=True, context={"request": request}
        )
        return Response(serializer.data)
