from django.http import Http404
from django.shortcuts import render

from .data import CHAPTERS, get_chapter


def design_previews(request):
    return render(request, "ledger/designs.html")


def trends(request):
    return render(request, "ledger/trends.html")


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
