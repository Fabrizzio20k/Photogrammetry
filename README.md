# Photogrametry
Fotogrametria en python acelerado por gpu

# Requisitos
- Docker
- NVIDIA Container Toolkit
- NVIDIA GPU con soporte para CUDA 12.0 o superior

Para instalar lo necesario, ya sea en windows WSL2 o en linux, siga las instrucciones de la siguiente URL:
https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html

# Instrucciones de instalacion
### Primero, debe de inicializar el docker de nvidia
```bash
docker build -t api .
```

### Luego, ejecute el docker
```bash
docker-compose up
```

### Finalmente, abra su navegador y vaya a la siguiente URL
```bash
http://localhost:8000/docs
```
