from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.utils import timezone

from .models import LoginSecurity


MAX_FAILED_ATTEMPTS = 3
LOCKOUT_MINUTES = 30


class SecureModelBackend(ModelBackend):

    def authenticate(
        self,
        request,
        username=None,
        password=None,
        **kwargs
    ):
        UserModel = get_user_model()

        if username is None:
            username = kwargs.get(
                UserModel.USERNAME_FIELD
            )

        if not username or password is None:
            return None

        username = username.strip()

        # =====================================================
        # LOCALIZA O USUÁRIO
        # =====================================================

        try:
            user = UserModel._default_manager.get(
                **{
                    UserModel.USERNAME_FIELD: username
                }
            )

        except UserModel.DoesNotExist:

            # Executa hash para reduzir diferenças de tempo
            # entre usuário existente e inexistente.
            UserModel().set_password(password)

            return None

        security, _ = LoginSecurity.objects.get_or_create(
            user=user
        )

        now = timezone.now()

        # =====================================================
        # BLOQUEIO ATIVO
        # =====================================================

        if (
            security.locked_until
            and security.locked_until > now
        ):
            return None

        # =====================================================
        # BLOQUEIO EXPIRADO
        # =====================================================

        if (
            security.locked_until
            and security.locked_until <= now
        ):
            security.failed_attempts = 0
            security.locked_until = None

            security.save(
                update_fields=[
                    "failed_attempts",
                    "locked_until",
                ]
            )

        # =====================================================
        # SENHA CORRETA
        # =====================================================

        if user.check_password(password):

            if not self.user_can_authenticate(user):
                return None

            # Login correto:
            # limpa qualquer falha anterior.
            if (
                security.failed_attempts != 0
                or security.locked_until is not None
            ):
                security.failed_attempts = 0
                security.locked_until = None

                security.save(
                    update_fields=[
                        "failed_attempts",
                        "locked_until",
                    ]
                )

            return user

        # =====================================================
        # SENHA INCORRETA
        # =====================================================

        security.failed_attempts = (
            security.failed_attempts or 0
        ) + 1

        security.last_failed_at = now

        if request is not None:
            security.last_failed_ip = self.get_client_ip(
                request
            )

        # =====================================================
        # TERCEIRA TENTATIVA
        # =====================================================

        if security.failed_attempts >= MAX_FAILED_ATTEMPTS:

            security.failed_attempts = MAX_FAILED_ATTEMPTS

            security.locked_until = (
                now
                + timedelta(
                    minutes=LOCKOUT_MINUTES
                )
            )

        security.save()

        return None

    @staticmethod
    def get_client_ip(request):

        forwarded_for = request.META.get(
            "HTTP_X_FORWARDED_FOR"
        )

        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        return request.META.get("REMOTE_ADDR")