from rest_framework import serializers

from .models import Task, TaskList


class TaskListSerializer(serializers.ModelSerializer):
    """Serializer de listas de tarefas (TaskList) do usuário autenticado."""

    class Meta:
        model = TaskList
        fields = ["id", "name", "description", "color", "user", "created_at"]
        read_only_fields = ["user", "created_at"] #read_only_fields faz os campos serem ignorados no payload de entrada, garantindo que o usuário não possa manipular esses campos ao criar ou atualizar uma TaskList.
                                                  #write_only_fields faz os campos serem ignorados no payload de saída, garantindo que o usuário não veja esses campos ao recuperar uma TaskList.

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
