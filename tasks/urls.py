from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    DashboardSummaryView,
    DashboardUpcomingView,
    SubTaskViewSet,
    TaskListViewSet,
    TaskViewSet,
)

app_name = "tasks"

router = DefaultRouter() #router é uma instância de DefaultRouter do Django REST Framework, que facilita a criação de rotas para viewsets, gerando automaticamente URLs para operações CRUD (Create, Read, Update, Delete) com base nos métodos definidos nos viewsets.
router.register("lists", TaskListViewSet, basename="tasklist")
router.register("tasks", TaskViewSet, basename="task")
router.register("subtasks", SubTaskViewSet, basename="subtask")

urlpatterns = [
    path(
        "dashboard/summary/", DashboardSummaryView.as_view(), name="dashboard-summary"
    ),
    path(
        "dashboard/upcoming/",
        DashboardUpcomingView.as_view(),
        name="dashboard-upcoming",
    ),
    path("", include(router.urls)),
]
