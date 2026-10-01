import json

from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods

from .asset_topics import ASSET_TOPICS, ASSET_TOPICS_BY_SLUG
from .data import CHAPTERS, get_chapter
from .forms import AssetForm
from .models import Asset

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


@ensure_csrf_cookie
def asset_management(request):
    assets = Asset.objects.all()
    context = {
        "asset_topics": ASSET_TOPICS,
        "category_choices": Asset.CATEGORY_CHOICES,
        "assets_json": json.dumps([_serialize_asset(a) for a in assets], ensure_ascii=False),
    }
    return render(request, "ledger/asset_management.html", context)


def _form_errors(form):
    return {field: [str(e) for e in errs] for field, errs in form.errors.items()}


@require_http_methods(["GET", "POST"])
def asset_api_list(request):
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


def asset_topic(request, slug):
    topic = ASSET_TOPICS_BY_SLUG.get(slug)
    if topic is None:
        raise Http404("존재하지 않는 주제입니다.")

    pos = ASSET_TOPICS.index(topic)
    prev_topic = ASSET_TOPICS[pos - 1] if pos > 0 else None
    next_topic = ASSET_TOPICS[pos + 1] if pos < len(ASSET_TOPICS) - 1 else None

    return render(request, "ledger/asset_topic.html", {
        "topic": topic,
        "prev_topic": prev_topic,
        "next_topic": next_topic,
        "asset_topics": ASSET_TOPICS,
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
