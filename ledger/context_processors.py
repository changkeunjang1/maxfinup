from .data import CHAPTERS


def nav_chapters(request):
    return {
        "nav_chapters": [{**c, "index": i} for i, c in enumerate(CHAPTERS, start=1)],
        "current_path": request.path,
    }
