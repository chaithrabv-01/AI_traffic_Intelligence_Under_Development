FROM python:3.11-slim
WORKDIR /code
# libgl/libglib: needed by OpenCV. ffmpeg: converts annotated video to browser-playable H.264.
RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 ffmpeg \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
# CPU-only PyTorch keeps the image much smaller. Remove this line if you set up GPU support.
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements.txt
COPY . .
