# Primera etapa: compilación
FROM nvidia/cuda:11.8.0-devel-ubuntu22.04 AS builder

# Evitar prompts durante la instalación
ENV DEBIAN_FRONTEND=noninteractive
ENV QT_XCB_GL_INTEGRATION=xcb_egl

# Actualizar sistema e instalar dependencias básicas
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    wget \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Instalar CMake más reciente
RUN wget https://github.com/Kitware/CMake/releases/download/v3.28.1/cmake-3.28.1-linux-x86_64.sh -q -O /tmp/cmake-install.sh \
    && chmod u+x /tmp/cmake-install.sh \
    && mkdir -p /opt/cmake \
    && /tmp/cmake-install.sh --skip-license --prefix=/opt/cmake \
    && ln -s /opt/cmake/bin/* /usr/local/bin/ \
    && rm /tmp/cmake-install.sh

# Instalar dependencias de compilación
RUN apt-get update && apt-get install -y --no-install-recommends \
    ninja-build \
    libboost-program-options-dev \
    libboost-graph-dev \
    libboost-system-dev \
    libeigen3-dev \
    libflann-dev \
    libmpfr-dev \
    libgmp-dev \
    libboost-thread-dev \
    libfreeimage-dev \
    libmetis-dev \
    libgoogle-glog-dev \
    libgtest-dev \
    libgmock-dev \
    libsqlite3-dev \
    libglew-dev \
    qtbase5-dev \
    libqt5opengl5-dev \
    libcgal-dev \
    libcgal-qt5-dev \
    libceres-dev \
    libopencv-dev \
    libboost-iostreams-dev \
    libboost-serialization-dev \
    libpng-dev \
    libjpeg-dev \
    libtiff-dev \
    libglu1-mesa-dev \
    nvidia-cuda-toolkit \
    nvidia-cuda-toolkit-gcc \
    python3 \
    python3-dev \
    python3-pip \
    python3-setuptools \
    python3-wheel \
    libcurl4-openssl-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Instalar Eigen 3.4 desde el código fuente
WORKDIR /opt
RUN git clone https://gitlab.com/libeigen/eigen.git --branch 3.4.0 eigen3 \
    && cd eigen3 \
    && mkdir build \
    && cd build \
    && cmake .. \
    && make install \
    && cd /opt \
    && rm -rf eigen3

# Instalar CGAL desde el código fuente
WORKDIR /opt
RUN git clone https://github.com/CGAL/cgal.git cgal \
    && cd cgal \
    && mkdir build \
    && cd build \
    && cmake -DCMAKE_BUILD_TYPE=Release .. \
    && make -j$(nproc) \
    && make install \
    && cd /opt \
    && rm -rf cgal

# Compilar COLMAP con soporte CUDA
WORKDIR /opt
RUN git clone https://github.com/colmap/colmap.git \
    && cd colmap \
    && git fetch \
    && mkdir build \
    && cd build \
    && cmake .. -GNinja -DCMAKE_CUDA_ARCHITECTURES=75 \
    -DCMAKE_BUILD_TYPE=Release \
    -DCUDA_ENABLED=ON \
    -DCMAKE_INSTALL_PREFIX=/usr/local \
    && ninja \
    && ninja install \
    && cd /opt \
    && rm -rf colmap

# Clonar y compilar VCGLib y OpenMVS
WORKDIR /opt
RUN git clone https://github.com/cdcseacave/VCG.git vcglib
RUN git clone https://github.com/cdcseacave/openMVS.git openMVS \
    && mkdir openMVS_build \
    && cd openMVS_build \
    && cmake ../openMVS -DCMAKE_BUILD_TYPE=Release -DVCG_ROOT="/opt/vcglib" -DENABLE_CUDA=ON -DCUDA_ARCH="75" -DCMAKE_INSTALL_PREFIX=/usr/local \
    && make -j$(nproc) \
    && make install \
    && cd /opt \
    && rm -rf openMVS openMVS_build vcglib

# Segunda etapa: imagen de ejecución
FROM nvidia/cuda:11.8.0-runtime-ubuntu22.04

# Evitar prompts durante la instalación
ENV DEBIAN_FRONTEND=noninteractive
ENV QT_XCB_GL_INTEGRATION=xcb_egl

# Instalar Python y pip
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Verificar qué paquetes están disponibles
RUN apt-get update && apt-cache search flann && apt-cache search cgal && apt-get clean

# Instalar todas las dependencias necesarias para ejecución con los nombres correctos
RUN apt-get update && apt-get install -y --no-install-recommends \
    libboost-program-options1.74.0 \
    libboost-filesystem1.74.0 \
    libboost-graph1.74.0 \
    libboost-system1.74.0 \
    libboost-thread1.74.0 \
    libboost-iostreams1.74.0 \
    libboost-serialization1.74.0 \
    libfreeimage3 \
    libgoogle-glog0v5 \
    libflann-dev \
    libglew2.2 \
    libsqlite3-0 \
    libqt5core5a \
    libqt5gui5 \
    libqt5widgets5 \
    libqt5opengl5 \
    libcurl4 \
    libcgal-dev \
    libgmp10 \
    libmpfr6 \
    libceres2 \
    libeigen3-dev \
    libopencv-core4.5d \
    libopencv-highgui4.5d \
    libopencv-imgproc4.5d \
    libopencv-imgcodecs4.5d \
    libopencv-calib3d4.5d \
    libopencv-features2d4.5d \
    libmetis5 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Copiar los binarios y librerías necesarias desde la etapa de compilación
COPY --from=builder /usr/local/bin/ /usr/local/bin/
COPY --from=builder /usr/local/lib/ /usr/local/lib/
COPY --from=builder /usr/local/include/ /usr/local/include/
COPY --from=builder /usr/local/share/ /usr/local/share/

# Actualizar la caché de librerías dinámicas
RUN ldconfig

# En runtime stage - instalar cmake del sistema SOLO para PyTorch
RUN apt-get update && apt-get install -y cmake && apt-get clean

# POR ESTO:
RUN pip install --no-cache-dir --force-reinstall --no-deps torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2 --index-url https://download.pytorch.org/whl/cu118
RUN pip install --no-cache-dir filelock typing-extensions sympy jinja2 networkx numpy pillow requests

# Resto de instalaciones
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
RUN pip install ultralytics --no-deps
RUN pip install --no-cache-dir pyyaml pillow matplotlib seaborn psutil py-cpuinfo pandas
RUN pip install --no-cache-dir --force-reinstall "numpy<2.0"

# Copiar la aplicación
COPY app.py /app/app.py
COPY utils/ /app/utils/
COPY models/ /app/models/

# Crear directorio de datos
RUN mkdir -p /data

# Establecer directorio de trabajo
WORKDIR /app

# Exponer puerto
EXPOSE 8000

# Comando para iniciar la API
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]