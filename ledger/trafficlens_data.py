"""TrafficLens(YOLO 과제) 소개 페이지 데이터: 발표 슬라이드 제목과 발표 대본."""

SLIDES = [
    {
        "n": 1,
        "image": "ledger/projects/trafficlens/slides/slide-01.jpg",
        "title": "TrafficLens",
        "notes": "안녕하세요, 팀 로드비전입니다. 저희가 만든 TrafficLens를 소개하겠습니다. 이번 과제로 YOLO를 이용해 도로 영상에서 차량과 보행자를 실시간으로 인식하고 개수를 세는 시스템을 만들었습니다.",
    },
    {
        "n": 2,
        "image": "ledger/projects/trafficlens/slides/slide-02.jpg",
        "title": "사람이 지켜보는 도로 감시는 느리고 놓치기 쉽다",
        "notes": "도로 감시를 사람이 하면 인력이 많이 들고, 위험 상황을 놓치기 쉽습니다. YOLO 같은 딥러닝 객체 탐지를 쓰면 이걸 자동화할 수 있습니다.",
    },
    {
        "n": 3,
        "image": "ledger/projects/trafficlens/slides/slide-03.jpg",
        "title": "세 가지를 만들고 확인한다",
        "notes": "목표는 세 가지입니다. 탐지, 카운팅, 그리고 모델별 성능 비교입니다.",
    },
    {
        "n": 4,
        "image": "ledger/projects/trafficlens/slides/slide-04.jpg",
        "title": "이미지를 한 번만 보고 위치와 종류를 동시에 맞힌다",
        "notes": "YOLO는 You Only Look Once의 약자로, 이미지를 한 번에 처리해 위치와 클래스를 같이 예측합니다. 그래서 실시간 처리에 유리합니다. 이번 과제는 YOLOv8을 사용했습니다.",
    },
    {
        "n": 5,
        "image": "ledger/projects/trafficlens/slides/slide-05.jpg",
        "title": "COCO 80개 클래스 중 교통 5개만 쓴다",
        "notes": "별도 학습 없이 COCO로 사전 학습된 가중치를 그대로 쓰고, 교통과 관련된 5개 클래스만 골라 탐지합니다.",
    },
    {
        "n": 6,
        "image": "ledger/projects/trafficlens/slides/slide-06.jpg",
        "title": "프레임마다 탐지 → 추적 → 카운팅",
        "notes": "매 프레임마다 YOLOv8로 탐지하고, ByteTrack으로 ID를 붙여 추적하고, 화면에 그은 기준선을 넘는 순간 방향별로 한 번만 셉니다. 사람이 아주 작게 나와서 더 큰 모델과 1280 해상도를 썼습니다.",
    },
    {
        "n": 7,
        "image": "ledger/projects/trafficlens/slides/slide-07.jpg",
        "title": "이동 경로가 기준선을 가로지르면 센다",
        "notes": "객체마다 직전 프레임의 중심점을 기억해 두었다가, 이번 프레임까지 이동한 경로가 기준선을 가로지르면 방향별로 1을 더합니다. 이미 센 ID는 다시 세지 않습니다.",
    },
    {
        "n": 8,
        "image": "ledger/projects/trafficlens/slides/slide-08.jpg",
        "title": "GPU로 바꾸자 탐지 속도가 10배 빨라졌다",
        "notes": "저희가 쓴 YOLOv8s 1280 설정은 CPU에서 초당 2.6프레임이었는데, GTX 1060 GPU로 바꾸니 27.8프레임으로 약 10배 빨라졌습니다. 추적과 영상 저장까지 포함한 전체 처리는 19분에서 4분으로 줄었습니다. 모델이 클수록 정확도는 오르지만 속도는 떨어집니다.",
    },
    {
        "n": 9,
        "image": "ledger/projects/trafficlens/slides/slide-09.jpg",
        "title": "90초 동안 승용차 146대가 기준선을 지났다",
        "notes": "삼성역 교차로 영상 90초를 처리한 결과입니다. 왼쪽 위 표에 지금 화면의 개수(now), 기준선 통과 수(line), 누적 수(total)가 나옵니다. 가운데 노란 선이 기준선이고, 차가 지나가면 초록색으로 깜빡입니다. 오른쪽 화면을 보시면 신호등이 사람으로 잘못 잡힌 것도 보이는데, 이건 뒤에서 한계로 말씀드리겠습니다.",
    },
    {
        "n": 10,
        "image": "ledger/projects/trafficlens/slides/slide-10.jpg",
        "title": "교통량은 그대로, 부풀린 total은 36% 줄였다",
        "notes": "앞에서 본 세 가지 문제를 고친 개선 버전입니다. 신호등은 탐지가 끊기며 ID가 계속 바뀌어서, ID가 아니라 위치로 판단했습니다. 영상 내내 '보행자'가 자주 나오는 자리는 고정 물체로 보고 뺐습니다. 또 추적 ID마다 가장 많이 나온 클래스를 쓰고, 아주 짧게 나타난 ID는 뺐습니다. 그 결과 교통량인 line은 151대로 그대로이고, 부풀려졌던 차량 total은 753에서 485로 36%, 보행자 total은 75에서 35로 줄었습니다. 다만 신호등 5개 중 2개는 남았고, 신호를 오래 기다리는 진짜 보행자도 빠질 수 있다는 한계가 있습니다.",
    },
    {
        "n": 11,
        "image": "ledger/projects/trafficlens/slides/slide-11.jpg",
        "title": "학습 없이도 교통량 집계가 가능했다",
        "notes": "정리하면, 별도 학습 없이 YOLOv8과 ByteTrack, 기준선만으로 90초 동안 승용차 146대를 방향별로 셀 수 있었습니다. GPU로 바꾸니 처리 속도가 약 5배 빨라졌지만 아직 실시간에는 못 미쳤고, 작은 보행자와 신호등 오탐지가 한계였습니다. 개선 버전으로 부풀려진 total은 36% 줄였지만 신호등 일부는 남았습니다. 다음 단계로 실시간 달성과 오탐지 줄이기를 해보고 싶습니다.",
    },
    {
        "n": 12,
        "image": "ledger/projects/trafficlens/slides/slide-12.jpg",
        "title": "감사합니다",
        "notes": "들어주셔서 감사합니다. 질문 있으시면 말씀해 주세요.",
    },
]
