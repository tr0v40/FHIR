def footer_listas(request):
    return {
        "footer_listas": [
            {
                "label": "Enxaqueca crise",
                "url": "/listas/enxaqueca/reducao-de-sintomas/",
            },
            {
                "label": "Enxaqueca controle",
                "url": "/listas/enxaqueca/controle/",
            },
        ]
    }