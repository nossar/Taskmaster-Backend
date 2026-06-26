from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import send_mail
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    ChangePasswordSerializer,
    LogoutSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
    UserSerializer,
    make_password_reset_token,
)

@extend_schema(summary="Cria um novo usuário (cadastro).",
               description="Cria um novo usuário (cadastro).",
               tags=["Usuários"],
               responses={201: RegisterSerializer})
class RegisterView(generics.CreateAPIView):
    """Cria um novo usuário (cadastro)."""

    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


class LogoutView(APIView):
    """Invalida (blacklist) o refresh token do usuário autenticado."""

    permission_classes = [IsAuthenticated]
    serializer_class = LogoutSerializer

    @extend_schema(
        summary="Logout (invalida o refresh token).",
        description="Invalida (blacklist) o refresh token do usuário autenticado.",
        tags=["Usuários"],
        responses={205: OpenApiResponse(description="Token invalidado com sucesso.")},
    )
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_205_RESET_CONTENT)


class PasswordResetRequestView(APIView):
    """Solicita a redefinição de senha por e-mail (esqueci minha senha)."""

    permission_classes = [AllowAny]
    serializer_class = PasswordResetRequestSerializer

    @extend_schema(
        summary="Esqueci minha senha.",
        description="Solicita a redefinição de senha por e-mail (esqueci minha senha).",
        tags=["Usuários"],
        responses={
            200: OpenApiResponse(
                description="Mensagem genérica de confirmação (não revela se o e-mail existe)."
            )
        },
    )
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        for user in User.objects.filter(email__iexact=email):
            uid, token = make_password_reset_token(user)
            reset_url = f"{settings.FRONTEND_URL}/reset-password?uid={uid}&token={token}"
            send_mail(
                subject="Taskmaster — Redefinição de senha",
                message=f"Use o link a seguir para redefinir sua senha: {reset_url}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
            )

        return Response(
            {
                "detail": "Se o e-mail informado estiver cadastrado, "
                "enviaremos um link de redefinição de senha."
            },
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(APIView):
    """Confirma a nova senha a partir do uid + token recebidos por e-mail."""

    permission_classes = [AllowAny]
    serializer_class = PasswordResetConfirmSerializer

    @extend_schema(
        summary="Confirma redefinição de senha.",
        description="Confirma a nova senha a partir do uid + token recebidos por e-mail.",
        tags=["Usuários"],
        responses={200: OpenApiResponse(description="Senha redefinida com sucesso.")},
    )
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Senha redefinida com sucesso."}, status=status.HTTP_200_OK)


@extend_schema_view(
    get=extend_schema(
        summary="Dados do usuário autenticado.",
        description="Retorna os dados do usuário autenticado (página do usuário).",
        tags=["Usuários"],
    ),
    patch=extend_schema(
        summary="Atualiza dados do usuário autenticado.",
        description="Atualiza parcialmente os dados da conta do usuário autenticado (ex.: e-mail).",
        tags=["Usuários"],
    ),
)
class MeView(generics.RetrieveUpdateAPIView):
    """Retorna ou atualiza os dados do usuário autenticado (página do usuário)."""

    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    """Troca a senha do usuário autenticado, exigindo a senha atual."""

    permission_classes = [IsAuthenticated]
    serializer_class = ChangePasswordSerializer

    @extend_schema(
        summary="Troca de senha.",
        description="Troca a senha do usuário autenticado, exigindo a senha atual.",
        tags=["Usuários"],
        responses={200: OpenApiResponse(description="Senha atualizada com sucesso.")},
    )
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Senha atualizada com sucesso."}, status=status.HTTP_200_OK)
