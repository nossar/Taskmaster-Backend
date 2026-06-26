from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import TaskListViewSet, TaskViewSet

app_name = "tasks"

router = DefaultRouter() #router é uma instância de DefaultRouter do Django REST Framework, que facilita a criação de rotas para viewsets, gerando automaticamente URLs para operações CRUD (Create, Read, Update, Delete) com base nos métodos definidos nos viewsets.
router.register("lists", TaskListViewSet, basename="tasklist")
router.register("tasks", TaskViewSet, basename="task")

urlpatterns = [
    path("", include(router.urls)),
]
