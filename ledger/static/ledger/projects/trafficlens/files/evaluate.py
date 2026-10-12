"""
모델 크기별 성능 비교 (보고서 6장 표 채우기용)
- mAP: COCO val 데이터로 측정 (처음 실행 시 데이터 자동 다운로드, 약 1GB)
- FPS: 테스트 영상 300프레임 평균

실행: python evaluate.py --video road.mp4
      python evaluate.py --video road.mp4 --skip-map   # FPS만 측정
"""
import argparse
import time

import cv2
from ultralytics import YOLO

MODELS = ["yolov8n.pt", "yolov8s.pt", "yolov8m.pt"]
CLASSES = [0, 2, 3, 5, 7]


def measure_fps(model, video, imgsz, n=300):
    cap = cv2.VideoCapture(video)
    frames = []
    while len(frames) < n:
        ret, f = cap.read()
        if not ret:
            break
        frames.append(f)
    cap.release()
    if not frames:
        raise SystemExit(f"영상을 읽을 수 없습니다: {video}")

    model(frames[0], classes=CLASSES, imgsz=imgsz, verbose=False)  # 워밍업
    start = time.time()
    for f in frames:
        model(f, classes=CLASSES, imgsz=imgsz, verbose=False)
    return len(frames) / (time.time() - start)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--video", default="road.mp4")
    p.add_argument("--skip-map", action="store_true")
    p.add_argument("--imgsz", default="640,1280", help="측정할 추론 해상도 목록")
    p.add_argument("--frames", type=int, default=300, help="FPS 측정 프레임 수")
    args = p.parse_args()

    sizes = [int(x) for x in args.imgsz.split(",")]
    print(f"{'모델':<12}{'imgsz':>7}{'mAP50-95':>10}{'mAP50':>10}{'FPS':>10}")
    for name in MODELS:
        model = YOLO(name)
        map95 = map50 = float("nan")
        if not args.skip_map:
            m = model.val(data="coco.yaml", classes=CLASSES, verbose=False)
            map95, map50 = m.box.map, m.box.map50
        for sz in sizes:
            fps = measure_fps(model, args.video, sz, args.frames)
            print(f"{name:<12}{sz:>7}{map95:>10.3f}{map50:>10.3f}{fps:>10.1f}", flush=True)

if __name__ == "__main__":
    main()
