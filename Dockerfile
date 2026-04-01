FROM nvidia/cuda:12.4.1-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# 시스템 의존성
RUN apt-get update && apt-get install -y \
    software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && apt-get install -y \
    python3.11 python3.11-venv python3.11-dev \
    python3-pip \
    blender \
    git wget curl unzip ninja-build \
    && rm -rf /var/lib/apt/lists/*

# Python 3.11을 기본으로
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1 && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

# pip 업그레이드
RUN python -m pip install --upgrade pip setuptools wheel

WORKDIR /app

# AutoRig3D 소스 복사
COPY pipeline/ /app/pipeline/
COPY server.py /app/server.py
COPY web/ /app/web/

# 웹 서버 의존성
RUN pip install requests python-dotenv fastapi uvicorn python-multipart

# UniRig 설치
RUN git clone https://github.com/VAST-AI-Research/UniRig /app/vendor/UniRig

WORKDIR /app/vendor/UniRig

# bpy 제거 (Docker 내 Blender는 시스템 패키지)
RUN sed -i '/^bpy/d' requirements.txt

# PyTorch + CUDA 12.4
RUN pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124

# UniRig 의존성
RUN pip install -r requirements.txt && \
    pip install numpy==1.26.4

# spconv (CUDA 12.x 호환 버전 시도)
RUN pip install cumm-cu120 || pip install cumm || true
RUN pip install spconv-cu120 || pip install spconv-cu121 || true

# 추가 의존성
RUN pip install lightning trimesh open3d pyrender || true
RUN pip install flash_attn || true

# VRM 애드온
RUN mkdir -p /root/.config/blender/4.0/scripts/addons/ && \
    wget -qO /tmp/vrm.zip \
    "https://github.com/saturday06/VRM-Addon-for-Blender/releases/download/v3.24.0/VRM_Addon_for_Blender-3_24_0.zip" && \
    unzip -qo /tmp/vrm.zip -d /root/.config/blender/4.0/scripts/addons/ && \
    rm /tmp/vrm.zip

WORKDIR /app

# output 디렉토리
RUN mkdir -p /app/output

EXPOSE 8000

# 기본: 웹 서버
CMD ["python", "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
