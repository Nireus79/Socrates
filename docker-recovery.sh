#!/bin/bash
set -e

echo "========================================="
echo "Docker Recovery and Setup Script"
echo "========================================="
echo ""

# Get to project directory
cd /mnt/c/Users/themi/PycharmProjects/Socrates

echo "[1/6] Stopping docker daemon and waiting for cleanup..."
sudo systemctl stop docker || true
sleep 3

echo "[2/6] Starting docker daemon..."
sudo systemctl start docker
sleep 5

echo "[3/6] Checking docker is responsive..."
sudo docker ps > /dev/null
echo "✓ Docker daemon is responsive"
echo ""

echo "[4/6] Stopping existing containers..."
sudo docker compose down -v || true
sleep 2

echo "[5/6] Building fresh images with new configuration..."
sudo docker compose build

echo "[6/6] Starting services..."
sudo docker compose up -d
sleep 5

echo ""
echo "========================================="
echo "Container Status:"
echo "========================================="
sudo docker compose ps

echo ""
echo "========================================="
echo "Health Checks:"
echo "========================================="
echo ""
echo "Testing reverse proxy health..."
curl -s http://localhost/health | head -c 100
echo ""
echo ""

echo "Testing API through reverse proxy..."
curl -s http://localhost/api/health 2>&1 | head -c 100
echo ""
echo ""

echo "========================================="
echo "Service Logs (last 20 lines of each):"
echo "========================================="
echo ""
echo "--- Redis Logs ---"
sudo docker compose logs redis | tail -20

echo ""
echo "--- API Logs ---"
sudo docker compose logs api | tail -20

echo ""
echo "--- Nginx/Web Logs ---"
sudo docker compose logs web | tail -20

echo ""
echo "========================================="
echo "Recovery Complete!"
echo "========================================="
echo ""
echo "If services are running and healthy, you can access:"
echo "  - Frontend: http://localhost"
echo "  - API health: http://localhost/api/health"
echo ""
