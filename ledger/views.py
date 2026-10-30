import json
import re
from urllib.parse import quote

from django.contrib.auth import login as auth_login
from django.contrib.auth.views import LoginView
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.templatetags.static import static
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods

from .asset_topics import ASSET_TOPICS, ASSET_TOPICS_BY_SLUG
from .data import CHAPTERS, get_chapter
from .forms import AssetForm, EmailLoginForm, SignupForm
from .membership import access_level
from .models import Asset
from .second_half import (
    BY_SLUG as SECOND_HALF_BY_SLUG, CHECKLIST as SECOND_HALF_CHECKLIST, CHECKLIST_COUNT as SECOND_HALF_CHECKLIST_COUNT,
    PILLARS as SECOND_HALF_PILLARS,
    SECTIONS as SECOND_HALF_SECTIONS,
)
from .second_half1 import (
    BY_SLUG as SECOND_HALF1_BY_SLUG, CHECKLIST as SECOND_HALF1_CHECKLIST, CHECKLIST_COUNT as SECOND_HALF1_CHECKLIST_COUNT,
    PILLARS as SECOND_HALF1_PILLARS,
    SECTIONS as SECOND_HALF1_SECTIONS,
)
from .trafficlens_data import LOGOS as TRAFFICLENS_LOGOS, SLIDES as TRAFFICLENS_SLIDES

CATEGORY_COLORS = {
    "real_estate": "#2a78d6",
    "deposit": "#eb6834",
    "securities": "#1baf7a",
    "insurance": "#eda100",
    "vehicle": "#e87ba4",
    "cash": "#008300",
    "other": "#4a3aa7",
}


def design_previews(request):
    return render(request, "ledger/designs.html")


def trends(request):
    return render(request, "ledger/trends.html")


def trafficlens(request):
    return render(request, "ledger/trafficlens.html", {"tl_tab": "overview", "slide_count": len(TRAFFICLENS_SLIDES), "logos": TRAFFICLENS_LOGOS})


def trafficlens_report(request):
    return render(request, "ledger/trafficlens_report.html", {"tl_tab": "report"})


def trafficlens_slides(request):
    slides_json = [
        {"n": s["n"], "title": s["title"], "notes": s["notes"], "url": static(s["image"])}
        for s in TRAFFICLENS_SLIDES
    ]
    context = {"tl_tab": "slides", "slides": TRAFFICLENS_SLIDES, "slides_json": slides_json}
    return render(request, "ledger/trafficlens_slides.html", context)


def _serialize_asset(asset):
    return {
        "id": asset.id,
        "name": asset.name,
        "category": asset.category,
        "category_label": asset.get_category_display(),
        "category_color": CATEGORY_COLORS.get(asset.category, "#4a3aa7"),
        "amount": str(asset.amount),
        "acquired_on": asset.acquired_on.isoformat() if asset.acquired_on else None,
        "memo": asset.memo,
    }


def _members_only(request, title, what):
    """비회원에게 보여 줄 잠금 화면(본문 없이 로그인·가입 안내만)."""
    return render(request, "ledger/members_only.html", {
        "title": title, "what": what, "access": access_level(request.user),
    })


def _staff_only_json(request):
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({"ok": False, "error": "관리자만 사용할 수 있습니다."}, status=403)
    return None


@never_cache
@ensure_csrf_cookie
def asset_management(request):
    if access_level(request.user) != "member":
        return _members_only(request, "자산관리", "자산관리")
    assets = Asset.objects.all()
    context = {
        "asset_topics": ASSET_TOPICS,
        "category_choices": Asset.CATEGORY_CHOICES,
        "assets_json": json.dumps([_serialize_asset(a) for a in assets], ensure_ascii=False),
    }
    context["access"] = "member"
    return render(request, "ledger/asset_management.html", context)


def _form_errors(form):
    return {field: [str(e) for e in errs] for field, errs in form.errors.items()}


@require_http_methods(["GET", "POST"])
def asset_api_list(request):
    denied = _staff_only_json(request)
    if denied:
        return denied
    if request.method == "POST":
        data = json.loads(request.body or "{}")
        form = AssetForm(data)
        if form.is_valid():
            asset = form.save()
            return JsonResponse({"ok": True, "asset": _serialize_asset(asset)}, status=201)
        return JsonResponse({"ok": False, "errors": _form_errors(form)}, status=400)

    assets = Asset.objects.all()
    return JsonResponse({"assets": [_serialize_asset(a) for a in assets]})


@require_http_methods(["PUT", "DELETE"])
def asset_api_detail(request, pk):
    denied = _staff_only_json(request)
    if denied:
        return denied
    asset = get_object_or_404(Asset, pk=pk)
    if request.method == "DELETE":
        asset.delete()
        return JsonResponse({"ok": True})

    data = json.loads(request.body or "{}")
    form = AssetForm(data, instance=asset)
    if form.is_valid():
        asset = form.save()
        return JsonResponse({"ok": True, "asset": _serialize_asset(asset)})
    return JsonResponse({"ok": False, "errors": _form_errors(form)}, status=400)


def experts(request):
    return render(request, "ledger/experts.html", {"asset_topics": ASSET_TOPICS})


@never_cache
def asset_topic(request, slug):
    topic = ASSET_TOPICS_BY_SLUG.get(slug)
    if topic is None:
        raise Http404("존재하지 않는 주제입니다.")
    if access_level(request.user) != "member":
        return _members_only(request, topic["title"], "자산관리 상세 내용")

    pos = ASSET_TOPICS.index(topic)
    prev_topic = ASSET_TOPICS[pos - 1] if pos > 0 else None
    next_topic = ASSET_TOPICS[pos + 1] if pos < len(ASSET_TOPICS) - 1 else None

    return render(request, "ledger/asset_topic.html", {
        "topic": topic,
        "prev_topic": prev_topic,
        "next_topic": next_topic,
        "asset_topics": ASSET_TOPICS,
        "access": "member",
    })


@never_cache
def second_half(request):
    pillars = [
        {**p, "sections": [s for s in SECOND_HALF_SECTIONS if s["pillar"] == p["key"]]}
        for p in SECOND_HALF_PILLARS
    ]
    return render(request, "ledger/second_half.html", {
        "sections": SECOND_HALF_SECTIONS,
        "pillars": pillars,
        "checklist": SECOND_HALF_CHECKLIST,
        "checklist_count": SECOND_HALF_CHECKLIST_COUNT,
        "access": access_level(request.user),
    })


def _with_heading_ids(html, slug):
    """Give each <h5> an anchor id and return (html, [(id, text), ...]) for the side contents."""
    toc = []

    def repl(m):
        anchor = f"{slug}-{len(toc) + 1}"
        toc.append((anchor, re.sub(r"<[^>]+>", "", m.group(1)).strip()))
        return f'<h5 id="{anchor}">{m.group(1)}</h5>'

    return re.sub(r"<h5>(.*?)</h5>", repl, html, flags=re.S), toc


@never_cache
def second_half_topic(request, slug):
    topic = SECOND_HALF_BY_SLUG.get(slug)
    if topic is None:
        raise Http404("존재하지 않는 주제입니다.")

    pos = SECOND_HALF_SECTIONS.index(topic)
    body_html, toc = _with_heading_ids(topic["html"], slug)
    access = access_level(request.user)
    if access != "member":
        # 비회원에게는 본문을 보내지 않는다. 첫 문단만 흐리게 미리 보여 준다.
        first = re.search(r"<p>.*?</p>", topic["html"], flags=re.S)
        preview_html, body_html, toc = (first.group(0) if first else ""), "", []
    else:
        preview_html = ""
    return render(request, "ledger/second_half_topic.html", {
        "topic": topic,
        "body_html": body_html,
        "preview_html": preview_html,
        "toc": toc,
        "pillar": next(p for p in SECOND_HALF_PILLARS if p["key"] == topic["pillar"]),
        "access": access,
        "sections": SECOND_HALF_SECTIONS,
        "prev_topic": SECOND_HALF_SECTIONS[pos - 1] if pos > 0 else None,
        "next_topic": SECOND_HALF_SECTIONS[pos + 1] if pos < len(SECOND_HALF_SECTIONS) - 1 else None,
    })


@never_cache
def second_half1(request):
    """인생 후반전1 — 2026 노트 정리본. 인생 후반전과 같은 회원 전용 규칙을 따른다."""
    pillars = [
        {**p, "sections": [s for s in SECOND_HALF1_SECTIONS if s["pillar"] == p["key"]]}
        for p in SECOND_HALF1_PILLARS
    ]
    return render(request, "ledger/second_half1.html", {
        "sections": SECOND_HALF1_SECTIONS,
        "pillars": pillars,
        "checklist": SECOND_HALF1_CHECKLIST,
        "checklist_count": SECOND_HALF1_CHECKLIST_COUNT,
        "access": access_level(request.user),
    })


@never_cache
def second_half1_topic(request, slug):
    topic = SECOND_HALF1_BY_SLUG.get(slug)
    if topic is None:
        raise Http404("존재하지 않는 주제입니다.")

    pos = SECOND_HALF1_SECTIONS.index(topic)
    body_html, toc = _with_heading_ids(topic["html"], slug)
    access = access_level(request.user)
    if access != "member":
        # 비회원에게는 본문을 보내지 않는다. 첫 문단만 흐리게 미리 보여 준다.
        first = re.search(r"<p>.*?</p>", topic["html"], flags=re.S)
        preview_html, body_html, toc = (first.group(0) if first else ""), "", []
    else:
        preview_html = ""
    return render(request, "ledger/second_half1_topic.html", {
        "topic": topic,
        "body_html": body_html,
        "preview_html": preview_html,
        "toc": toc,
        "access": access,
        "pillar": next(p for p in SECOND_HALF1_PILLARS if p["key"] == topic["pillar"]),
        "sections": SECOND_HALF1_SECTIONS,
        "prev_topic": SECOND_HALF1_SECTIONS[pos - 1] if pos > 0 else None,
        "next_topic": SECOND_HALF1_SECTIONS[pos + 1] if pos < len(SECOND_HALF1_SECTIONS) - 1 else None,
    })


class MemberLoginView(LoginView):
    template_name = "ledger/auth_login.html"
    authentication_form = EmailLoginForm
    redirect_authenticated_user = True


def _safe_next(request, default="ledger:second_half"):
    nxt = request.POST.get("next") or request.GET.get("next") or ""
    if nxt and url_has_allowed_host_and_scheme(nxt, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return nxt
    return default


def signup(request):
    if request.user.is_authenticated:
        return redirect(_safe_next(request))
    form = SignupForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        auth_login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        nxt = _safe_next(request, "")
        return redirect(reverse("ledger:signup_done") + (f"?next={quote(nxt)}" if nxt else ""))
    return render(request, "ledger/auth_signup.html", {"form": form, "next": _safe_next(request, "")})


def signup_done(request):
    return render(request, "ledger/auth_signup_done.html", {
        "access": access_level(request.user), "next": _safe_next(request, ""),
    })


def privacy_policy(request):
    return render(request, "ledger/privacy_policy.html")


def terms(request):
    return render(request, "ledger/terms.html")


def email_refusal(request):
    return render(request, "ledger/email_refusal.html")


def home(request):
    chapters = [{**ch, "index": i, "count": len(ch["entries"])} for i, ch in enumerate(CHAPTERS, start=1)]
    return render(request, "ledger/home.html", {"chapters": chapters, "total_entries": sum(ch["count"] for ch in chapters)})


def chapter_detail(request, slug):
    chapter = get_chapter(slug)
    if chapter is None:
        raise Http404("존재하지 않는 편입니다.")

    ch_index = next(i for i, c in enumerate(CHAPTERS, start=1) if c["slug"] == slug)
    entries = []
    for entry in chapter["entries"]:
        e = dict(entry)
        e["id"] = "e" + entry["n"].replace(".", "-")
        entries.append(e)

    all_slugs = [c["slug"] for c in CHAPTERS]
    pos = all_slugs.index(slug)
    prev_chapter = CHAPTERS[pos - 1] if pos > 0 else None
    next_chapter = CHAPTERS[pos + 1] if pos < len(CHAPTERS) - 1 else None

    context = {
        "chapter": chapter,
        "chapter_index": ch_index,
        "entries": entries,
        "prev_chapter": prev_chapter,
        "next_chapter": next_chapter,
    }
    return render(request, "ledger/chapter.html", context)
