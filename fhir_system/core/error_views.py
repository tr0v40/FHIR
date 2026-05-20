from django.shortcuts import render


def error_404_en(request, exception):
    return render(
        request,
        "404_en.html",
        status=404
    )


def error_500_en(request):
    return render(
        request,
        "500_en.html",
        status=500
    )