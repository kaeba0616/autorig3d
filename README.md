# AutoRig3D

이미지 한 장 → 리깅된 3D 모델 + VRM 자동 생성

캐릭터 일러스트를 넣으면 AI가 3D 모델로 변환하고, Blender가 자동으로 19개 본 스켈레톤을 리깅하고, VSeeFace에서 바로 쓸 수 있는 VRM 파일까지 만들어줍니다.

## 파이프라인

```
이미지 (PNG/JPG)
  → [Step 1] Meshy AI가 3D 메쉬 생성 (1-5분)
  → [Step 2] Blender가 19개 본 자동 리깅 (5-10초)
  → [Step 3] VRM 자동 변환 (5초)
  → VSeeFace에서 바로 VTuber 방송 가능!
```

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

[Meshy](https://meshy.ai) 가입 후 API 키를 `.env` 파일에 추가:

```bash
# .env 파일 생성
echo "MESHY_API_KEY=여기에_meshy_api_키" > .env
```

## 사용법

### 방법 1: 웹 UI (추천)

```bash
cd autorig3d
source .venv/bin/activate
python3 server.py
```

1. http://localhost:8000 접속
2. 캐릭터 이미지를 드래그앤드롭
3. 1-5분 대기 (진행 상황 표시됨)
4. 완료되면 VRM / GLB / FBX 다운로드

### 방법 2: CLI

```bash
cd autorig3d
source .venv/bin/activate
python3 -m pipeline.run 캐릭터이미지.png
```

### 방법 3: 기존 리깅 모델만 VRM 변환

이미 리깅된 GLB/FBX가 있다면 VRM 변환만 할 수 있습니다:

```bash
source .venv/bin/activate
python3 -c "
from pipeline.vrm_convert import convert_to_vrm
convert_to_vrm('output/내모델/rigged_model.glb', 'output/내모델')
"
```

## 출력 구조

결과는 `output/{이미지이름}/` 폴더에 저장됩니다:

```
output/
└── miku/
    ├── original.jpg        ← 원본 이미지
    ├── model.glb           ← 3D 메쉬 (리깅 전)
    ├── rigged_model.glb    ← 리깅된 모델 (19개 본)
    └── model.vrm           ← VRM 파일 (VSeeFace용)
```

## VTuber로 사용하기

1. output 폴더에서 `model.vrm` 파일을 찾습니다
2. [VSeeFace](https://www.vseeface.icu/) 설치 (Windows, 무료)
3. VSeeFace 실행 → VRM 파일 로드
4. 웹캠을 켜면 페이스 트래킹이 시작됩니다

## 리깅 스켈레톤 (19개 본)

```
Hips
├── Spine → Chest → Neck → Head
├── Shoulder.L → UpperArm.L → LowerArm.L → Hand.L
├── Shoulder.R → UpperArm.R → LowerArm.R → Hand.R
├── UpperLeg.L → LowerLeg.L → Foot.L
└── UpperLeg.R → LowerLeg.R → Foot.R
```

VRM 표준 휴머노이드 본 매핑이 자동으로 설정됩니다.

## 파일 포맷 비교

| 포맷 | 용도 | 열 수 있는 프로그램 |
|------|------|-------------------|
| **VRM** | VTuber 전용 | VSeeFace, VRoid, Luppet |
| **GLB** | 범용 3D | Blender, Unity, Windows 3D 뷰어 |
| **FBX** | 범용 3D | Blender, Maya, Unity, Unreal Engine |

## 기술 스택

- Python 3.12+
- [Meshy API](https://meshy.ai) — 이미지 → 3D 모델 변환
- [Blender](https://www.blender.org/) 4.0+ — 자동 리깅 (headless)
- [VRM Addon for Blender](https://github.com/saturday06/VRM-Addon-for-Blender) — VRM 변환
- [FastAPI](https://fastapi.tiangolo.com/) — 웹 서버

## 문제 해결

### Meshy API 오류
- API 키가 `.env`에 올바르게 설정되었는지 확인
- Meshy 무료 크레딧이 남아있는지 확인: https://meshy.ai

### Blender 리깅 실패
- `blender --version`으로 4.0 이상인지 확인
- GLB 내보내기 실패 시 자동으로 FBX로 폴백됩니다

### VRM 변환 실패
- VRM 애드온이 설치되었는지 확인: `ls ~/.config/blender/4.0/scripts/addons/VRM_Addon_for_Blender-release/`
- VRM 변환이 실패해도 GLB/FBX 파일은 정상 생성됩니다
