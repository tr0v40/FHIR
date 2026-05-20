from django.shortcuts import render



def custom_404(request, exception):

    path = request.path.lower()

    english_routes = [
        "/treatments/",
        "/trestments/",
        "/treatment/",
        "/treat/"
    ]

    if any(route in path for route in english_routes):
        return render(request, "404_en.html", status=404)

    return render(request, "404.html", status=404)


def error_500_en(request):
    return render(
        request,
        "500_en.html",
        status=500
    )