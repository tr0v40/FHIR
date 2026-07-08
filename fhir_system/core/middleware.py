from django.shortcuts import render


class DomainRoutingMiddleware:
    """
    Bloqueia páginas em inglês fora do domínio inglês.
    Não interfere na home /.
    """

    ENGLISH_HOSTS = {
        "www.telix.health",
        "telix.health",
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(":")[0]
        path = request.path

        # Só bloqueia rotas em inglês fora do domínio inglês
        if path.startswith("/treatments/") and host not in self.ENGLISH_HOSTS:
            return render(
                request,
                "404_pt.html",
                status=404
            )

        return self.get_response(request)