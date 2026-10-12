"""
TrafficLens (팀 로드비전) - YOLO 기반 도로 위 차량·보행자 실시간 인식 시스템
- YOLOv8 + ByteTrack 으로 차량/보행자를 탐지·추적
- 화면에 기준선을 긋고, 기준선을 통과한 차량/보행자를 방향별로 카운팅
- 현재 화면 속 개수(now), 기준선 통과 수(line), 누적 고유 ID 수(total), FPS 표시, 결과 영상 저장
- 개선 기능 (기본으로 켜짐, --baseline 으로 끔)
    1) 위치 기반 정지 물체 필터: 영상 내내 '보행자'가 자주 나오는 자리(신호등 등)의 보행자는 제외
    2) 클래스 다수결: 추적 ID별로 가장 많이 나온 클래스를 사용 (트럭<->버스 혼동 방지)
    3) 짧은 추적 제거: 몇 프레임만 보인 ID는 total 에서 제외

실행 예)
    python traffic_detect.py                               # road.mp4, 개선 버전
    python traffic_detect.py --baseline                    # 개선 기능 끄기 (비교용)
    python traffic_detect.py --source 0                    # 웹캠
    python traffic_detect.py --model yolov8n.pt --imgsz 640  # 빠른 설정
    python traffic_detect.py --line 0.1,0.6,0.9,0.6        # 가로 기준선 (x1,y1,x2,y2 비율)
    python traffic_detect.py --save ""                     # 영상 저장 끄기 (더 빠름)
"""
import argparse
import time
from collections import Counter, defaultdict

import cv2
import torch
from ultralytics import YOLO

# COCO 클래스 ID -> 화면 표시 이름 (OpenCV는 한글 출력이 안 되어 영문 사용)
TARGET_CLASSES = {
    0: "Person",
    2: "Car",
    3: "Motorcycle",
    5: "Bus",
    7: "Truck",
}
VEHICLE_IDS = {2, 3, 5, 7}

# 클래스별 박스 색 (BGR)
COLORS = {
    0: (0, 200, 255),   # 보행자: 주황
    2: (255, 120, 0),   # 승용차: 파랑
    3: (200, 0, 200),   # 오토바이: 보라
    5: (0, 200, 0),     # 버스: 초록
    7: (0, 0, 220),     # 트럭: 빨강
}
LINE_COLOR = (0, 255, 255)     # 기준선: 노랑
FLASH_COLOR = (0, 255, 0)      # 통과 순간: 초록
STATIC_COLOR = (150, 150, 150)  # 정지 물체로 제외: 회색


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--source", default="road.mp4", help="영상 경로 또는 웹캠 번호(0)")
    p.add_argument("--model", default="yolov8s.pt", help="yolov8n/s/m/l/x.pt")
    p.add_argument("--imgsz", type=int, default=1280, help="추론 해상도 (작은 보행자는 1280 권장)")
    p.add_argument("--conf", type=float, default=0.4, help="차량 신뢰도 임계값")
    p.add_argument("--person-conf", type=float, default=0.25, help="보행자 신뢰도 임계값 (작아서 낮게)")
    p.add_argument("--line", default="0.45,0.28,0.45,0.85",
                   help="기준선 x1,y1,x2,y2 (화면 크기 대비 0~1 비율)")
    p.add_argument("--save", default="result.mp4", help="결과 저장 경로 (빈 값이면 저장 안 함)")
    p.add_argument("--device", default=None, help="0 = 첫 번째 GPU, cpu = CPU (기본: GPU가 있으면 GPU)")
    p.add_argument("--no-show", action="store_true", help="화면 창을 띄우지 않음")
    # 개선 기능
    p.add_argument("--baseline", action="store_true", help="개선 기능을 끄고 기본 버전으로 실행")
    p.add_argument("--static-seconds", type=float, default=20, help="이 시간이 지난 뒤부터 정지 물체 판단")
    p.add_argument("--static-cell", type=int, default=32, help="정지 판단용 칸 크기 (1080p 기준 픽셀)")
    p.add_argument("--static-ratio", type=float, default=0.15,
                   help="지금까지 프레임의 이 비율 이상 '보행자'가 나온 칸 = 고정 물체")
    p.add_argument("--min-track", type=int, default=5, help="이보다 짧게(프레임) 보인 ID는 total 에서 제외")
    return p.parse_args()


def side(p, a, b):
    """점 p가 선분 a-b의 어느 쪽에 있는지 (+/-/0)."""
    return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])


def crossed(p_prev, p_now, a, b):
    """이전 위치 -> 현재 위치 이동이 기준선 a-b를 가로질렀으면 방향(+1/-1), 아니면 0."""
    s1, s2 = side(p_prev, a, b), side(p_now, a, b)
    if s1 == 0 or s1 * s2 > 0:
        return 0
    # 이동 경로의 양 끝이 기준선 양쪽에 있어도, 선분 범위 밖이면 통과가 아님
    t1, t2 = side(a, p_prev, p_now), side(b, p_prev, p_now)
    if t1 * t2 > 0:
        return 0
    return 1 if s2 > 0 else -1


class TotalCounter:
    """클래스별 total(누적 고유 ID 수)을 관리한다.

    기본 버전: 탐지된 클래스마다 ID를 따로 센다 (같은 ID가 트럭·버스 양쪽에 들어갈 수 있음).
    개선 버전: ID마다 다수결 클래스 하나로 세고, 짧은 추적과 정지 물체는 뺀다.
               바뀐 ID만 다시 반영해서 매 프레임 전체를 다시 세지 않는다.
    """

    def __init__(self, improved, min_track):
        self.improved, self.min_track = improved, min_track
        self.votes = defaultdict(Counter)   # ID별 클래스 투표
        self.seen = Counter()               # ID별 등장 프레임 수
        self.static = set()                 # 정지 물체로 판정된 ID
        self.raw = defaultdict(set)         # 기본 버전용: 클래스별 ID
        self.state = {}                     # 개선 버전용: ID -> 지금 total 에 들어가 있는 클래스
        self.counts = Counter()             # 개선 버전용: 클래스별 total

    def voted(self, tid):
        return self.votes[tid].most_common(1)[0][0]

    def _refresh(self, tid):
        new = None
        if self.seen[tid] >= self.min_track and tid not in self.static:
            new = self.voted(tid)
        old = self.state.get(tid)
        if new != old:
            if old is not None:
                self.counts[old] -= 1
            if new is not None:
                self.counts[new] += 1
            self.state[tid] = new

    def add(self, tid, cls):
        self.raw[cls].add(tid)
        self.votes[tid][cls] += 1
        self.seen[tid] += 1
        if self.improved:
            self._refresh(tid)

    def mark_static(self, tid):
        if tid not in self.static:
            self.static.add(tid)
            self._refresh(tid)

    def get(self, cls):
        return self.counts[cls] if self.improved else len(self.raw[cls])


def draw_panel(frame, current, line_count, totals, fps, tag):
    """왼쪽 위에 현재(now) / 기준선 통과(line) / 누적(total) 개수와 FPS 패널을 그린다."""
    def passed(cids):
        return sum(line_count[c][1] + line_count[c][-1] for c in cids)

    def total(cids):
        return sum(totals.get(c) for c in cids)

    # 표 형태: 이름 | now | line | total (글자 폭이 달라 열 위치를 고정해서 그림)
    rows = [("", "now", "line", "total")]
    groups = [("Vehicles", VEHICLE_IDS), ("Persons", [0])]
    groups += [("  " + TARGET_CLASSES[c], [c]) for c in (2, 3, 5, 7)]
    for name, cids in groups:
        rows.append((name, str(sum(current[c] for c in cids)), str(passed(cids)), str(total(cids))))

    col_x = [22, 260, 380, 500]
    h = 30 * (len(rows) + 1) + 16
    overlay = frame.copy()
    cv2.rectangle(overlay, (10, 10), (610, 10 + h), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.55, frame, 0.45, 0, frame)
    cv2.putText(frame, f"FPS: {fps:.1f}  [{tag}]", (22, 42), cv2.FONT_HERSHEY_SIMPLEX,
                0.75, (255, 255, 255), 2, cv2.LINE_AA)
    for i, cells in enumerate(rows):
        y = 42 + 30 * (i + 1)
        color = (180, 180, 180) if i == 0 else (255, 255, 255)
        for x, text in zip(col_x, cells):
            cv2.putText(frame, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.75, color, 2, cv2.LINE_AA)


def main():
    args = parse_args()
    source = int(args.source) if args.source.isdigit() else args.source
    improved = not args.baseline
    tag = "improved" if improved else "baseline"

    device = args.device if args.device is not None else (0 if torch.cuda.is_available() else "cpu")
    print(f"실행 장치: {torch.cuda.get_device_name(0) if device != 'cpu' else 'CPU'} | 모드: {tag}")

    model = YOLO(args.model)
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        raise SystemExit(f"영상을 열 수 없습니다: {args.source}")

    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps_in = cap.get(cv2.CAP_PROP_FPS) or 30
    lx1, ly1, lx2, ly2 = map(float, args.line.split(","))
    A, B = (int(lx1 * w), int(ly1 * h)), (int(lx2 * w), int(ly2 * h))

    writer = None
    if args.save:
        writer = cv2.VideoWriter(args.save, cv2.VideoWriter_fourcc(*"mp4v"), fps_in, (w, h))

    last_pos = {}                                         # 추적 ID -> 직전 프레임 중심점
    counted = set()                                       # 이미 센 추적 ID (한 번만 셈)
    totals = TotalCounter(improved, args.min_track)       # total (누적 고유 ID)
    line_count = defaultdict(lambda: {1: 0, -1: 0})       # 클래스별 방향별 통과 수
    heat = Counter()                                      # 칸별 '보행자'가 나온 프레임 수 (정지 판단용)
    cell = max(int(args.static_cell * w / 1920), 1)       # 해상도에 맞춘 칸 크기
    static_frames = int(args.static_seconds * fps_in)
    flash = 0                                             # 통과 순간 기준선 강조 남은 프레임
    prev = start = time.time()
    fps = 0.0
    idx = 0
    min_conf = min(args.conf, args.person_conf)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # 탐지 + 추적 (persist=True: 프레임 간 ID 유지)
        results = model.track(frame, classes=list(TARGET_CLASSES), conf=min_conf, imgsz=args.imgsz, device=device,
                              persist=True, tracker="bytetrack.yaml", verbose=False)
        boxes = results[0].boxes

        current = defaultdict(int)
        person_cells = set()
        if boxes is not None and len(boxes):
            ids = boxes.id.int().tolist() if boxes.id is not None else [None] * len(boxes)
            for xyxy, cls, conf, tid in zip(boxes.xyxy.tolist(), boxes.cls.int().tolist(),
                                            boxes.conf.tolist(), ids):
                # 클래스별 임계값: 보행자는 낮게, 차량은 높게
                if conf < (args.person_conf if cls == 0 else args.conf):
                    continue
                x1, y1, x2, y2 = map(int, xyxy)
                center = ((x1 + x2) // 2, (y1 + y2) // 2)

                if tid is not None:
                    totals.add(tid, cls)
                    if improved:
                        cls = totals.voted(tid)                           # 클래스 다수결

                # 위치 기반 정지 물체 필터: 이 자리(주변 3x3 칸)에 '보행자'가 너무 자주 나왔으면 제외
                is_static = False
                if cls == 0:
                    gx, gy = center[0] // cell, center[1] // cell
                    person_cells.add((gx, gy))
                    if improved and idx >= static_frames:
                        ratio = max(heat[(gx + dx, gy + dy)] for dx in (-1, 0, 1) for dy in (-1, 0, 1)) / idx
                        is_static = ratio >= args.static_ratio
                if is_static:
                    if tid is not None:
                        totals.mark_static(tid)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), STATIC_COLOR, 1)
                    continue

                current[cls] += 1
                if tid is not None:
                    if tid in last_pos and tid not in counted:
                        d = crossed(last_pos[tid], center, A, B)
                        if d:
                            line_count[cls][d] += 1
                            counted.add(tid)
                            flash = 6
                    last_pos[tid] = center

                color = COLORS[cls]
                label = f"{TARGET_CLASSES[cls]} {conf:.2f}" + (f" #{tid}" if tid is not None else "")
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.circle(frame, center, 3, color, -1)
                (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                cv2.rectangle(frame, (x1, y1 - th - 8), (x1 + tw + 6, y1), color, -1)
                cv2.putText(frame, label, (x1 + 3, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX,
                            0.5, (255, 255, 255), 1, cv2.LINE_AA)
        heat.update(person_cells)                                         # 칸별 보행자 등장 횟수 누적

        # 기준선 (누가 통과하면 잠깐 초록색으로 깜빡임)
        cv2.line(frame, A, B, FLASH_COLOR if flash else LINE_COLOR, 4, cv2.LINE_AA)
        cv2.putText(frame, "COUNT LINE", (A[0] + 10, A[1] - 12), cv2.FONT_HERSHEY_SIMPLEX,
                    0.8, LINE_COLOR, 2, cv2.LINE_AA)
        flash = max(flash - 1, 0)

        # FPS (지수 이동 평균으로 부드럽게)
        now = time.time()
        fps = 0.9 * fps + 0.1 * (1.0 / max(now - prev, 1e-6)) if fps else 1.0 / max(now - prev, 1e-6)
        prev = now

        draw_panel(frame, current, line_count, totals, fps, tag)

        if writer:
            writer.write(frame)
        if not args.no_show:
            cv2.imshow("TrafficLens - Vehicle & Pedestrian Detection", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
        idx += 1

    cap.release()
    if writer:
        writer.release()
    cv2.destroyAllWindows()

    elapsed = time.time() - start
    print(f"=== 결과 [{tag}]: {idx} 프레임, {elapsed:.0f}초 (평균 {idx / max(elapsed, 1e-6):.1f} FPS) ===")
    print("클래스      기준선 통과 (방향 + / 방향 - / 합계) | total")
    for cid, name in TARGET_CLASSES.items():
        c = line_count[cid]
        print(f"{name:<10}: {c[1]:4d} / {c[-1]:4d} / {c[1] + c[-1]:4d} | total {totals.get(cid):4d}")
    if improved:
        print(f"정지 물체로 제외한 ID: {len(totals.static)}개")


if __name__ == "__main__":
    main()
