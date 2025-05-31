# Photogrametry
Fotogrametria en python acelerado por gpu

# Requisitos
- Docker
- NVIDIA Container Toolkit
- NVIDIA GPU con soporte para CUDA

Para instalar lo necesario, ya sea en windows WSL2 o en linux, siga las instrucciones de la siguiente URL:
https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html

# Instrucciones de instalacion
### Primero, debe de inicializar el docker de nvidia
```bash
docker build -t api .
```

### Luego, ejecute el archivo run.sh
```bash
sh run.sh
```

### Finalmente, abra su navegador y vaya a la siguiente URL
```bash
http://localhost:8000/docs
```