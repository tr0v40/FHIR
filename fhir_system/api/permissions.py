from rest_framework.permissions import BasePermission


class IntegracaoReadCreateUpdatePermission(BasePermission):
    """
    Permite leitura, criação e edição para usuários autorizados.
    Bloqueia exclusão.
    """

    usuarios_autorizados = ["diuary", "anaB"]

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.username not in self.usuarios_autorizados:
            return False

        return request.method in ["GET", "HEAD", "OPTIONS", "POST", "PUT", "PATCH"]