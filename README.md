# AutoRig3D

이미지 한 장 → 3D 모델 + 자동 리깅 + VRM 생성

캐릭터 일러스트를 넣으면 AI가 3D 모델로 변환하고, 자동으로 스켈레톤을 리깅합니다.

## 파이프라인

두 가지 모드를 지원합니다:

```
🧊 3D 모델만:
이미지 → [Meshy AI] → GLB 3D 모델

🎮 전체 파이프라인:
이미지 → [Meshy AI] → GLB → [Blender 리깅] → FBX/GLB → [VRM 변환] → VSeeFace
```

| 단계 | 도구 | 소요 시간 |
|------|------|----------|
| 3D 모델 생성 | Meshy API | 1-5분 |
| 자동 리깅 (Blender) | Blender headless | 5-10초 |
| 자동 리깅 (UniRig AI) | UniRig + GPU | 1-2분 |
| VRM 변환 | Blender VRM addon | 5초 |

## 설치

### 1. 필수 프로그램

```bash
# Blender 설치 (4.0+)
sudo apt install blender

# VRM 애드온 설치
curl -sL -o /tmp/vrm_addon.zip "https://github.com/saturday06/VRM-Addon-for-Blender/releases/download/v3.24.0/VRM_Addon_for_Blender-3_24_0.zip"
mkdir -p ~/.config/blender/4.0/scripts/addons/
unzip -qo /tmp/vrm_addon.zip -d ~/.config/blender/4.0/scripts/addons/
```

### 2. Python 환경

```bash
git clone https://github.com/kaeba0616/autorig3d.git
cd autorig3d
python3 -m venv .venv
source .venv/bin/activate
pip install requests python-dotenv fastapi uvicorn python-multipart
```

### 3. API 키 설정

[Meshy](https://meshy.ai) 가입 후 `.env` 파일 생성:

```bash
echo "MESHY_API_KEY=여기에_meshy_api_키" > .env
```

### 4. (선택) UniRig AI 리깅 — GPU 있는 경우

RTX 5080/5090 등 GPU가 있으면 UniRig로 AI 리깅 가능:

```bash
./setup_unirig.sh
```

GPU 없으면 Blender 템플릿 리깅이 자동으로 사용됩니다.

## 사용법

### 웹 UI (추천)

```bash
source .venv/bin/activate
python3 server.py
```

http://localhost:8000 접속:
- **🧊 3D 모델만** — 이미지 → GLB 3D 모델 (리깅 없음)
- **🎮 전체 파이프라인** — 이미지 → 3D → 리깅 → VRM

이미지를 드래그앤드롭하면 1-5분 후 결과 다운로드 가능.

### CLI

```bash
source .venv/bin/activate

# 전체 파이프라인 (3D + 리깅 + VRM)
python3 -m pipeline.run 캐릭터이미지.png

# 3D 모델만 생성
python3 -c "
from pipeline.mesh_gen import image_to_3d
image_to_3d('캐릭터이미지.png', './output/모델명')
"

# UniRig AI 리깅 사용 (GPU 필요)
python3 -m pipeline.run 캐릭터이미지.png --mode unirig

# Blender 리깅만 사용
python3 -m pipeline.run 캐릭터이미지.png --mode blender
```

### Colab (GPU 없는 경우 UniRig 사용)

[colab/AutoRig3D_UniRig.ipynb](colab/AutoRig3D_UniRig.ipynb)를 Colab에서 열고:

1. 런타임 → T4 GPU 선택
2. 셀 순서대로 실행
3. GLB 업로드 → 리깅된 모델 다운로드

### VRM 변환만

이미 리깅된 GLB/FBX가 있다면:

```bash
python3 -c "
from pipeline.vrm_convert import convert_to_vrm
convert_to_vrm('output/모델명/rigged_model.glb', 'output/모델명')
"
```

## 출력 구조

```
output/
└── 캐릭터이름/
    ├── original.jpg        ← 원본 이미지
    ├── model.glb           ← 3D 메쉬 (리깅 전)
    ├── rigged_model.glb    ← 리깅된 모델 (또는 .fbx)
    └── model.vrm           ← VRM (VTuber용)
```

## 리깅 모드 비교

| 모드 | 도구 | 장점 | 단점 |
|------|------|------|------|
| **auto** (기본) | UniRig → Blender 폴백 | 최선의 결과 자동 선택 | UniRig 미설치 시 Blender로 |
| **unirig** | UniRig (SIGGRAPH 2025) | AI가 메쉬 분석, 최고 품질 | GPU 필요 (8GB+ VRAM) |
| **blender** | Blender 템플릿 | GPU 불필요, 빠름 | 고정 본 비율, 비표준 체형에 약함 |

## 리깅 스켈레톤 (19개 본)

```
Hips
├── Spine → Chest → Neck → Head
├── Shoulder.L → UpperArm.L → LowerArm.L → Hand.L
├── Shoulder.R → UpperArm.R → LowerArm.R → Hand.R
├── UpperLeg.L → LowerLeg.L → Foot.L
└── UpperLeg.R → LowerLeg.R → Foot.R
```

## VTuber로 사용하기

1. `output/모델명/model.vrm` 다운로드
2. [VSeeFace](https://www.vseeface.icu/) 설치 (Windows, 무료)
3. VSeeFace → VRM 로드 → 웹캠 켜면 페이스 트래킹 시작

## 기술 스택

- Python 3.12+
- [Meshy API](https://meshy.ai) — 이미지 → 3D 모델
- [Blender](https://www.blender.org/) 4.0+ — 리깅 + VRM 변환
- [UniRig](https://github.com/VAST-AI-Research/UniRig) — AI 자동 리깅 (SIGGRAPH 2025)
- [VRM Addon](https://github.com/saturday06/VRM-Addon-for-Blender) — VRM 변환
- [FastAPI](https://fastapi.tiangolo.com/) — 웹 서버

## 문제 해결

| 문제 | 해결 |
|------|------|
| Meshy API 오류 | `.env`에 키 확인, 무료 크레딧 남았는지 확인 |
| Blender GLB 내보내기 실패 | 자동으로 FBX로 폴백됨 (정상) |
| VRM 변환 실패 | VRM 애드온 설치 확인. GLB/FBX는 정상 생성됨 |
| UniRig 설치 실패 | `./setup_unirig.sh` 다시 실행, conda 필요 |
| GPU 없음 | Blender 모드 자동 사용, 또는 Colab 노트북 이용 |
