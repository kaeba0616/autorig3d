# AutoRig3D

이미지 한 장 → 리깅된 3D 모델 자동 생성

캐릭터 일러스트를 넣으면 AI가 3D 모델로 변환하고, Blender가 자동으로 19개 본 스켈레톤을 리깅합니다.

## 파이프라인

```
이미지 (PNG/JPG) → [Meshy AI] → 3D 메쉬 (GLB) → [Blender] → 리깅된 모델 (GLB/FBX)
```

| 단계 | 도구 | 소요 시간 |
|------|------|----------|
| 3D 모델 생성 | Meshy API | 1-5분 |
| 자동 리깅 | Blender (headless) | 5-10초 |

## 설치

### 1. 필수 프로그램

```bash
# Blender (4.0+)
sudo apt install blender

# Python 가상환경
cd autorig3d
python3 -m venv .venv
source .venv/bin/activate
pip install requests python-dotenv fastapi uvicorn python-multipart
```

### 2. API 키 설정

[Meshy](https://meshy.ai) 가입 후 API 키를 `.env` 파일에 추가:

```bash
# .env
MESHY_API_KEY=여기에_meshy_api_키
```

## 사용법

### 웹 UI (추천)

```bash
source .venv/bin/activate
python3 server.py
```

http://localhost:8000 접속 → 캐릭터 이미지 드래그 → 완료 후 다운로드

### CLI

```bash
source .venv/bin/activate
python3 -m pipeline.run 캐릭터이미지.png
```

## 출력 구조

결과는 `output/{이미지이름}/` 폴더에 저장됩니다:

```
output/
└── miku/
    ├── original.jpg        ← 원본 이미지
    ├── model.glb           ← 3D 메쉬 (리깅 전)
    └── rigged_model.glb    ← 리깅된 모델 (19개 본)
```

## 리깅 스켈레톤 (19개 본)

```
Hips
├── Spine → Chest → Neck → Head
├── Shoulder.L → UpperArm.L → LowerArm.L → Hand.L
├── Shoulder.R → UpperArm.R → LowerArm.R → Hand.R
├── UpperLeg.L → LowerLeg.L → Foot.L
└── UpperLeg.R → LowerLeg.R → Foot.R
```

## 결과 파일 사용법

- **GLB 파일**: Windows 3D 뷰어, Blender, Unity, Unreal Engine에서 바로 열기
- **FBX 파일**: Blender, Maya, Unity에서 열기
- **VTuber 사용**: GLB → VRM 변환 후 VSeeFace에서 사용 가능

## 기술 스택

- Python 3.12+
- Meshy API (이미지 → 3D)
- Blender 4.0+ (자동 리깅, headless)
- FastAPI (웹 서버)
