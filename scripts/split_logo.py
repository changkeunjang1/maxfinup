"""One-off: split the supplied compass+wordmark PNG into an icon crop and a
text-wordmark crop, with white made transparent, for use in the site header."""
import os
import numpy as np
from PIL import Image

SRC = r"C:\Users\mbc\Documents\카카오톡 받은 파일\KakaoTalk_20260911_165737561.png"
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "ledger", "static", "ledger", "brand")

WHITE_THRESHOLD = 245


def make_transparent(im: Image.Image) -> Image.Image:
    im = im.convert("RGBA")
    arr = np.array(im)
    rgb = arr[:, :, :3]
    is_white = np.all(rgb >= WHITE_THRESHOLD, axis=-1)
    arr[is_white, 3] = 0
    return Image.fromarray(arr, "RGBA")


def content_columns(arr) -> np.ndarray:
    alpha = arr[:, :, 3]
    return alpha.max(axis=0) > 0


def tight_crop(im: Image.Image) -> Image.Image:
    bbox = im.getbbox()
    return im.crop(bbox) if bbox else im


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    im = make_transparent(Image.open(SRC))
    arr = np.array(im)
    cols = content_columns(arr)

    # find the gap (run of empty columns) between icon and wordmark
    idx = np.where(cols)[0]
    first, last = idx[0], idx[-1]
    gaps = []
    run_start = None
    for x in range(first, last + 1):
        if not cols[x]:
            if run_start is None:
                run_start = x
        else:
            if run_start is not None:
                gaps.append((run_start, x - 1))
                run_start = None
    gaps = [g for g in gaps if g[1] - g[0] > 5]
    split = gaps[0][0] + (gaps[0][1] - gaps[0][0]) // 2 if gaps else (first + last) // 2

    icon = tight_crop(im.crop((0, 0, split, im.height)))
    wordmark = tight_crop(im.crop((split, 0, im.width, im.height)))

    icon.save(os.path.join(OUT_DIR, "compass-icon.png"))
    wordmark.save(os.path.join(OUT_DIR, "wordmark.png"))
    print("icon size", icon.size)
    print("wordmark size", wordmark.size)


if __name__ == "__main__":
    main()
