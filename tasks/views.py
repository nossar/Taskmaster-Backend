from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Task, TaskList
from .serializers import TaskListSerializer, TaskSerializer


class TaskListViewSet(viewsets.ModelViewSet):
    """CRUD de listas de tarefas (TaskList) pertencentes ao usuário autenticado."""

    serializer_class = TaskListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self): #get_queryset é um método que retorna o conjunto de dados (queryset) que será usado para as operações do viewset. Aqui, ele filtra as listas de tarefas para incluir apenas aquelas pertencentes ao usuário autenticado, garantindo que cada usuário só veja suas próprias listas.
        if getattr(self, "swagger_fake_view", False): #caso a view seja uma visualização fake do Swagger (gerada para documentação), retorna um queryset vazio para evitar erros de serialização.
            return TaskList.objects.none()
        return TaskList.objects.filter(user=self.request.user).order_by("name")

    def perform_create(self, serializer): 
        #perform_create é um método que é chamado quando uma nova instância do modelo está sendo criada, chamado após a validação do serializer. Aqui, ele garante que o campo 'user' da TaskList seja automaticamente definido como o usuário autenticado, evitando que o usuário possa manipular esse campo no payload da requisição.
        serializer.save(user=self.request.user)


class TaskViewSet(viewsets.ModelViewSet):
    """CRUD de tarefas, restritas ao usuário autenticado."""

    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

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
