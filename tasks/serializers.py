from rest_framework import serializers

from .models import SubTask, Task, TaskList


class TaskListSerializer(serializers.ModelSerializer):
    """Serializer de listas de tarefas (TaskList) do usuário autenticado."""

    pending_count = serializers.SerializerMethodField()

    class Meta:
        model = TaskList
        fields = [
            "id",
            "name",
            "description",
            "color",
            "user",
            "created_at",
            "pending_count",
        ]
        read_only_fields = ["user", "created_at"] #read_only_fields faz os campos serem ignorados no payload de entrada, garantindo que o usuário não possa manipular esses campos ao criar ou atualizar uma TaskList.
                                                  #write_only_fields faz os campos serem ignorados no payload de saída, garantindo que o usuário não veja esses campos ao recuperar uma TaskList.

    def get_pending_count(self, obj) -> int:
        # getattr com fallback: fora do queryset anotado pelo viewset (ex.: após create()), o campo não existe na instância.
        return getattr(obj, "pending_count", 0)

class TaskSerializer(serializers.ModelSerializer):
    """Serializer de tarefas (Task), vinculadas a uma TaskList do usuário autenticado."""

    class Meta:
        model = Task
        fields = [
            "id",
            "task_list",
            "owner",
            "title",
            "description",
            "priority",
            "status",
            "due_date",
            "planned_date",
            "done",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["owner", "created_at", "updated_at"]

    def __init__(self, *args, **kwargs): #init roda sempre que o serializer é instanciado, permitindo customizar o comportamento do serializer com base no contexto da requisição.
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request is not None and request.user.is_authenticated:
            # Evita que o usuário vincule a task a uma lista de terceiros.
            self.fields["task_list"].queryset = TaskList.objects.filter(
                user=request.user
            )


class DashboardSummarySerializer(serializers.Serializer):
    """Contagens agregadas exibidas no painel inicial do dashboard."""

    pending = serializers.IntegerField()
    overdue = serializers.IntegerField()
    today = serializers.IntegerField()
    completed_week = serializers.IntegerField()


class SubTaskSerializer(serializers.ModelSerializer):
    """Serializer de subtarefas (SubTask), vinculadas a uma Task do usuário autenticado."""

    class Meta:
        model = SubTask
        fields = ["id", "task", "title", "done", "created_at"]
        read_only_fields = ["created_at"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request is not None and request.user.is_authenticated:
            # Evita que o usuário vincule a subtask a uma task de terceiros.
            self.fields["task"].queryset = Task.objects.filter(
                task_list__user=request.user
            )
