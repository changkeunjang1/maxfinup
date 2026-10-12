"""TrafficLens 서브도메인(trafficlens.maxfinup.com) 연결.

- 서브도메인의 /, /report/, /slides/ 를 /projects/trafficlens/ 하위 페이지로 내부 연결한다.
- 서브도메인으로 들어온 그 밖의 주소(경영장부 글 등)는 본 사이트로 보낸다.
- 본 사이트의 /projects/trafficlens/... 는 서브도메인 주소로 영구 이동시킨다.
"""
from django.conf import settings
from django.http import HttpResponsePermanentRedirect

TL_PREFIX = "/projects/trafficlens"
TL_PAGES = ("/", "/report/", "/slides/")
PASS_THROUGH = ("/static/", "/favicon.ico", "/robots.txt")


def _host(request):
    return request.META.get("HTTP_HOST", "").split(":")[0].lower()


class TrafficLensSubdomainMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.tl_host = getattr(settings, "TRAFFICLENS_HOST", "")
        self.main_hosts = set(getattr(settings, "TRAFFICLENS_MAIN_HOSTS", ()))
        self.main_url = getattr(settings, "MAIN_SITE_URL", "").rstrip("/")

    def __call__(self, request):
        request.tl_subdomain = False
        if not self.tl_host:
            return self.get_response(request)

        host, path = _host(request), request.path_info
        query = request.META.get("QUERY_STRING", "")
        suffix = f"?{query}" if query else ""

        if host == self.tl_host:
            if path.startswith(PASS_THROUGH):
                return self.get_response(request)
            if path.startswith(TL_PREFIX + "/"):
                return HttpResponsePermanentRedirect(path[len(TL_PREFIX):] + suffix)
            if path + "/" in TL_PAGES:
                return HttpResponsePermanentRedirect(path + "/" + suffix)
            if path in TL_PAGES:
                request.tl_subdomain = True
                request.path_info = TL_PREFIX + path
                request.path = request.path_info
                return self.get_response(request)
            return HttpResponsePermanentRedirect(f"{self.main_url}{path}{suffix}")

        if host in self.main_hosts and (path == TL_PREFIX or path.startswith(TL_PREFIX + "/")):
            rest = path[len(TL_PREFIX):] or "/"
            return HttpResponsePermanentRedirect(f"https://{self.tl_host}{rest}{suffix}")

        return self.get_response(request)
