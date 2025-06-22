#!/bin/bash
# Simplified script to speed up Docker build without using BuildKit caching

# Enable BuildKit features
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# Display build start message
echo "Starting optimized build process..."

# Optional - clean up any dangling images first
docker image prune -f

# Build using BuildKit without external caching
docker build \
  --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
  -f /mnt/.ix-apps/docker/myapps/inventor/Dockerfile \
  -t videoinventory \
  /mnt/.ix-apps/docker/myapps/inventor

BUILD_SUCCESS=$?

# Report success/failure
if [ $BUILD_SUCCESS -eq 0 ]; then
  echo "✅ Build completed successfully!"
else
  echo "❌ Build failed with exit code $BUILD_SUCCESS"
fi

exit $BUILD_SUCCESS