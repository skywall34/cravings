#!/bin/bash
set -e

PAT_TOKEN=$1

IMAGE_NAME="cravings"
TAG="prod"
REGISTRY="ghcr.io"
USERNAME="skywall34"
FULL_IMAGE_NAME="$REGISTRY/$USERNAME/$IMAGE_NAME:$TAG"

echo "Building Docker image..."
docker build --no-cache -t "$IMAGE_NAME:$TAG" .

echo "Tagging image as $FULL_IMAGE_NAME"
docker tag "$IMAGE_NAME:$TAG" "$FULL_IMAGE_NAME"

echo "Logging in to $REGISTRY"
echo $PAT_TOKEN | docker login "$REGISTRY" -u $USERNAME --password-stdin

echo "Pushing image to $FULL_IMAGE_NAME"
docker push "$FULL_IMAGE_NAME"

echo "Done!"
