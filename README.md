# Study Planner Agent API

Một AI agent tối giản giúp biến mục tiêu học tập thành kế hoạch theo tuần. Agent hiện dùng logic deterministic và các tool nội bộ nên chạy được ngay, không cần API key hay dịch vụ bên ngoài.

## Tính năng

- FastAPI backend với OpenAPI tại `/docs`.
- Agent phân tích mục tiêu, chọn module phù hợp và tạo lịch học theo số giờ mỗi tuần.
- Logging JSON đầy đủ: request id, thời gian xử lý, endpoint, status code, lỗi và event nghiệp vụ.
- Health check, validation bằng Pydantic và error response thống nhất.
- Test API bằng pytest.

## Chạy local

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python -m uvicorn app.main:app --reload
```

Mở `http://127.0.0.1:8000/docs`.

## Ví dụ gọi API

```powershell
$body = @{
  goal = "Học Python để xây dựng API backend"
  weekly_hours = 6
  weeks = 4
  current_level = "beginner"
  preferred_days = @("Mon", "Wed", "Fri")
} | ConvertTo-Json

Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/api/v1/agent/study-plan `
  -ContentType "application/json" `
  -Body $body
```

## Chạy test

```powershell
python -m pytest -q
```

## Chạy bằng Docker Compose

Yêu cầu Docker Desktop hoặc Docker Engine có Compose v2:

```powershell
docker compose up --build -d
docker compose ps
Invoke-RestMethod http://127.0.0.1:8000/health
docker compose logs -f app
```

Dừng service:

```powershell
docker compose down
```

Compose chạy app dưới user non-root, bật health check, giới hạn capability và lưu log vào volume `app_logs`.

## CI/CD deploy lên EC2

Workflow nằm tại `.github/workflows/ci-cd.yml` và hoạt động như sau:

```text
Pull Request -> test + compile + Docker build
push main   -> test -> build/push GHCR -> deploy dev -> deploy production -> health check/rollback
```

### Chuẩn bị EC2

EC2 cần Linux, Docker Engine và Docker Compose v2. User SSH phải chạy được Docker (thường thêm user vào group `docker` rồi đăng nhập lại). Security Group chỉ nên mở port 22 từ IP runner/địa chỉ quản trị và port ứng dụng hoặc reverse proxy theo nhu cầu.

Tạo thư mục deploy, ví dụ `/opt/study-planner-agent`. User SSH cần có Docker và `sudo` không hỏi password để workflow tạo/chown thư mục deploy. Workflow tự copy `compose.yaml`, `.env.example` và thư mục `observability`; lần đầu nó tạo `.env` từ `.env.example` nếu chưa có.

### GitHub Actions secrets

Tạo cùng bộ secrets trong cả hai environment `dev` và `production`; mỗi environment chứa giá trị EC2 tương ứng:

| Secret | Nội dung |
|---|---|
| `EC2_HOST` | Public DNS hoặc IP của EC2 |
| `EC2_USER` | User SSH, ví dụ `ubuntu` hoặc `ec2-user` |
| `EC2_APP_DIR` | Đường dẫn tuyệt đối, ví dụ `/opt/study-planner-agent` |
| `EC2_SSH_PRIVATE_KEY` | Private key SSH tương ứng public key trên EC2 |

Không đưa private key hoặc `.env` production vào Git. Workflow dùng `GITHUB_TOKEN` để push image; image GHCR phải public vì EC2 không còn đăng nhập GHCR. Push vào `main` sẽ deploy dev trước, sau đó production; có thể bật required reviewers cho environment `production` để thêm bước duyệt thủ công.

### Lưu ý rollback

Trước khi thay container, workflow lưu image đang chạy. Nếu container mới không chuyển sang trạng thái `healthy` sau tối đa 60 giây, workflow in log và khởi động lại image trước đó. Khi deploy lần đầu chưa có image cũ, job sẽ fail để tránh che giấu lỗi cấu hình.

## Logging

Mặc định log JSON được ghi ra stdout. Có thể ghi thêm ra file bằng cách đặt `LOG_FILE=logs/app.log` trong `.env`. Mỗi request có `request_id` và response trả lại id đó trong header `X-Request-ID`.

Ví dụ một log event:

```json
{"timestamp":"2026-10-04T00:00:00+00:00","level":"INFO","logger":"app.http","message":"request.completed","request_id":"...","method":"POST","path":"/api/v1/agent/study-plan","status_code":200,"duration_ms":2.41}
```

## Cấu trúc

```text
app/
  agent.py            # agent orchestration và domain logic
  config.py           # cấu hình từ environment
  logging_config.py   # JSON logging + request context
  main.py             # FastAPI application
  models.py           # request/response schemas
  tools.py            # tool nội bộ cho agent
tests/
  test_api.py
```

## Observability

Compose khởi động sẵn Prometheus, Grafana, Loki, Tempo và Alloy:

- Grafana: `http://127.0.0.1:3000` (`admin` / `GRAFANA_ADMIN_PASSWORD`)
- Prometheus: `http://127.0.0.1:9090`
- Loki: `http://127.0.0.1:3100`
- Tempo HTTP API: `http://127.0.0.1:3200`
- App metrics: `http://127.0.0.1:8000/metrics`

Grafana được provision sẵn datasource Prometheus, Loki và Tempo. Alloy đọc log JSON từ volume `app_logs` và gửi vào Loki. Tempo mở OTLP gRPC/HTTP lần lượt ở cổng `4317`/`4318` để nhận trace.

Đổi `GRAFANA_ADMIN_PASSWORD` trong `.env` trước khi dùng ngoài máy local. Dùng `docker compose down -v` chỉ khi muốn xóa toàn bộ dữ liệu metrics, logs và dashboard local.
