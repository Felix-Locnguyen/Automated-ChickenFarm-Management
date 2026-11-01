#!/usr/bin/env bash
# 08_scripts/deploy.sh — một lệnh dựng cả hệ thống bằng Docker
# Cách chạy (từ BẤT KỲ đâu):
#   bash 08_scripts/deploy.sh
# Yêu cầu: Docker + Docker Compose v2 (docker compose version)
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="$REPO_ROOT/05_docker/docker-compose.yml"

echo "=== 🐔 Automated Chicken Farm — deploy (Docker) ==="

# 0. Kiểm tra Docker
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker chưa chạy hoặc bạn chưa có quyền (thử: sudo usermod -aG docker \$USER rồi đăng nhập lại)"
    exit 1
fi

# 1. Tạo .env nếu chưa có (bí mật: SECRET_KEY, mật khẩu DB/MinIO)
if [ ! -f "$REPO_ROOT/05_docker/.env" ]; then
    cp "$REPO_ROOT/05_docker/.env.example" "$REPO_ROOT/05_docker/.env"
    echo "✅ Đã tạo 05_docker/.env từ .env.example (đổi SECRET_KEY trước khi deploy thật!)"
fi

# 2. Build + khởi động toàn bộ service
echo "⏳ Building image + khởi động container (lần đầu mất vài phút)..."
docker compose -f "$COMPOSE_FILE" up -d --build

# 3. Chờ backend healthy rồi seed dữ liệu mẫu (nếu DB trống)
echo "⏳ Chờ backend sẵn sàng..."
for i in $(seq 1 30); do
    if docker inspect -f '{{.State.Health.Status}}' farm-backend 2>/dev/null | grep -q healthy; then
        break
    fi
    sleep 2
done

echo "🌱 Seed dữ liệu mẫu (admin@farm.vn / admin123)..."
docker compose -f "$COMPOSE_FILE" exec backend python ../08_scripts/seed/data.py || \
    echo "ℹ️  (DB đã có dữ liệu — bỏ qua seed)"

cat <<EOF

=== ✅ Hệ thống đang chạy ===
  🌐 Web:          http://localhost:8080   (login: admin@farm.vn / admin123)
  📡 API docs:     http://localhost:8020/docs
  🗄️  MinIO console: http://localhost:9001   (farmminio / farmminio123 — trong .env)
  📦 Trạng thái:   docker compose -f 05_docker/docker-compose.yml ps
  📜 Logs backend: docker compose -f 05_docker/docker-compose.yml logs -f backend
  ⏹️  Dừng:        docker compose -f 05_docker/docker-compose.yml down
EOF
