#!/bin/sh

set -e

IMAGE_NAME=ellinashurovsk-thesis-image
CONTAINER_NAME=ellinashurovsk-thesis-container

sudo docker container stop $CONTAINER_NAME || true
sudo docker build -t $IMAGE_NAME -f docker/Dockerfile .
sudo docker run --rm --name $CONTAINER_NAME --user "$(id -u)" -v "$(pwd)/data":/app/data $IMAGE_NAME
