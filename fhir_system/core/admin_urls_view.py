# core/admin_urls_view.py
from django.contrib.admin.views.decorators import staff_member_required
from django.urls import get_resolver
from django.shortcuts import render

def _iter_patterns(urlpatterns, prefix=""):
    for p in urlpatterns:
        if hasattr(p, "url_patterns"): 
            yield from _iter_patterns(p.url_patterns, prefix + str(p.pattern))
        else:
            yield {
                "pattern": prefix + str(p.pattern),
                "name": p.name or "",
                "lookup_str": getattr(p, "lookup_str", ""),
            }

@staff_member_required
def admin_urls_list(request):
    resolver = get_resolver()
    rows = list(_iter_patterns(resolver.url_patterns))

    
    rows.sort(key=lambda r: r["pattern"])

    return render(request, "admin/urls_list.html", {"rows": rows})