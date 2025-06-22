#!/bin/bash
# Script to speed up Docker build by using BuildKit and layer caching

# Create cache directory
mkdir -p /tmp/.buildx-cache

# Enable BuildKit features
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# Display build start message
echo "Starting optimized build process..."

# Optional - clean up any dangling images first
docker image prune -f

# Build using BuildKit with caching
docker build \
  --build-arg BUILDKIT_INLINE_CACHE=1 \
  --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
  --cache-from=type=local,src=/tmp/.buildx-cache \
  --cache-to=type=local,dest=/tmp/.buildx-cache-new,mode=max \
  -f /mnt/.ix-apps/docker/myapps/inventor/Dockerfile \
  -t videoinventory \
  /mnt/.ix-apps/docker/myapps/inventor

BUILD_SUCCESS=$?

# Rotate the cache for next build
if [ -d /tmp/.buildx-cache-new ]; then
  rm -rf /tmp/.buildx-cache
  mv /tmp/.buildx-cache-new /tmp/.buildx-cache
fi

# Report success/failure
if [ $BUILD_SUCCESS -eq 0 ]; then
  echo "✅ Build completed successfully!"
else
  echo "❌ Build failed with exit code $BUILD_SUCCESS"
fi

exit $BUILD_SUCCESS