docker stop api-container
docker rm api-container
docker run -p 8000:8000 --gpus all \
  -v $(pwd)/data:/data \
  --name api-container api