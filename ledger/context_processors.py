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
        "tl_urls": {"overview": base + "/", "report": base + "/report/", "slides": base + "/slides/"},
    }


def member_menus(request):
    """헤더의 회원 전용 메뉴(자산관리 · 인생 후반전 · 인생 후반전1)는 관리자와 승인 회원에게만 보인다."""
    from .membership import access_level
    user = getattr(request, "user", None)
    return {"show_member_menus": bool(user) and access_level(user) == "member"}
