from django.shortcuts import redirect
from core import public_views_en


ENGLISH_HOSTS = {
    "www.telix.health",
    "telix.health",
}


def domain_home(request):
    host = request.get_host().split(":")[0]

    if host in ENGLISH_HOSTS:
        return public_views_en.english_treatments_home(request)

    return redirect("https://www.telix.inf.br/")