from django.conf import settings

from .data import CHAPTERS


def nav_chapters(request):
    return {
        "nav_chapters": [{**c, "index": i} for i, c in enumerate(CHAPTERS, start=1)],
        "current_path": request.path,
    }


def trafficlens_urls(request):
    """TrafficLens 페이지 링크: 서브도메인에서는 짧은 주소, 그 밖에서는 /projects/trafficlens/ 주소."""
    sub = getattr(request, "tl_subdomain", False)
    base = "" if sub else "/projects/trafficlens"
    return {
        "tl_subdomain": sub,
        "main_site_url": settings.MAIN_SITE_URL.rstrip("/"),
        "tl_urls": {"overview": base + "/", "report": base + "/report/", "slides": base + "/slides/"},
    }
