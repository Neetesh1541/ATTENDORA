# ATTENDORA — Production Deployment Manual

This guide covers complete, production-grade deployment strategies for **ATTENDORA**:
- **Option 1 (Recommended):** Turnkey Single-Command Docker Compose (VPS, AWS EC2, DigitalOcean, Hetzner, or On-Premise)
- **Option 2:** 1-Click Cloud PaaS Deploy (Render.com / Railway.app)
- **Option 3:** High-Performance Serverless Hybrid (Vercel Edge Frontend + Render/Railway Backend + Neon/Supabase Postgres)
- **Option 4:** Bare-Metal Linux Server (Ubuntu systemd + Nginx + Let's Encrypt SSL)

---

## ⚡ Option 1: Turnkey Docker Compose (Recommended)

This is the fastest and most robust self-hosted deployment. It launches:
- **`attendora-db`**: PostgreSQL 16 with automatic data persistence
- **`attendora-backend`**: FastAPI with OpenCV + dlib + face_recognition + auto-migration
- **`attendora-frontend`**: Nginx with reverse proxy to backend, WebSocket support, and static asset caching

### Step 1: Transfer Files to Your Server
Copy the `attendora` project directory to your Linux server (e.g. `/opt/attendora`):
```bash
scp -r attendora user@your-server-ip:/opt/
ssh user@your-server-ip
cd /opt/attendora
```

### Step 2: Configure Environment Variables
Create a root `.env` file (or customize `docker-compose.yml` defaults):
```bash
cat << 'EOF' > .env
# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=ChangeThisSecurePassword!2026
POSTGRES_DB=attendora

# Security Key (Generate with: openssl rand -hex 32)
SECRET_KEY=9a2b8e39d1045f2084c8a143e1104e768e7d21c4b79103e5c9a4192b6a5e1284

# CORS: Set your domain name here
ALLOWED_ORIGINS=https://attendora.yourdomain.com,http://localhost

# Initial Super Admin (created on first run)
SUPER_ADMIN_EMAIL=admin@yourdomain.com
SUPER_ADMIN_PASSWORD=StrongAdminPassword!2026
EOF
```

### Step 3: Launch Containers
```bash
# Build and start all services in detached mode
docker compose up -d --build

# View container logs
docker compose logs -f
```

The system is now live:
- **Web SaaS Interface:** `http://your-server-ip`
- **Backend REST API:** `http://your-server-ip:8000/api`
- **API Documentation:** `http://your-server-ip:8000/docs`

---

### Step 4: Configure Domain & Free SSL (Let's Encrypt / Certbot)

To access your SaaS over secure `https://attendora.yourdomain.com`:

1. Point an `A` record in your DNS provider (e.g. Cloudflare, Namecheap, GoDaddy):
   - **Host:** `@` or `attendora`
   - **Target:** `your-server-ip`

2. Install Certbot on the host machine:
```bash
sudo apt update && sudo apt install -y nginx certbot python3-certbot-nginx
```

3. Configure host Nginx as SSL terminating reverse proxy (`/etc/nginx/sites-available/attendora`):
```nginx
server {
    server_name attendora.yourdomain.com;

    location / {
        proxy_pass http://localhost:80;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

4. Obtain and install free SSL certificate:
```bash
sudo ln -s /etc/nginx/sites-available/attendora /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d attendora.yourdomain.com
```

---

## ☁️ Option 2: 1-Click Deploy on Render.com

The repository includes a ready-to-use [`render.yaml`](file:///c:/Users/neete/OneDrive/ドキュメント/attendora/render.yaml) blueprint.

1. Push your repository to **GitHub** or **GitLab**.
2. Log in to [Render.com](https://render.com/).
3. Click **New +** → **Blueprint**.
4. Connect your Attendora repository.
5. Render will automatically detect `render.yaml` and provision:
   - Managed PostgreSQL database
   - Containerized FastAPI backend with persistent 10GB media disk
   - React static frontend with routing rewrites
6. Click **Apply**. In approximately 3 minutes, your full SaaS is live with free auto-renewing SSL certificates.

---

## ⚡ Option 3: Hybrid Vercel (Frontend) + Render/Railway (Backend)

For global edge performance with lowest latency:

### 1. Database (PostgreSQL)
- Create a free instance on [Neon.tech](https://neon.tech) or [Supabase.com](https://supabase.com).
- Copy the PostgreSQL connection URI (e.g., `postgresql+asyncpg://user:pass@ep-xyz.neon.tech/attendora`).

### 2. Backend (FastAPI on Railway / Render)
- Connect GitHub repo and specify root directory as `backend`.
- Set Environment Variables:
  - `DATABASE_URL`: Your connection string from Step 1.
  - `SECRET_KEY`: Long random string (`openssl rand -hex 32`).
  - `ALLOWED_ORIGINS`: `*` or your Vercel domain.
- Deploy. Note your public backend URL (e.g., `https://attendora-api.up.railway.app`).

### 3. Frontend (Vercel)
- Go to [Vercel](https://vercel.com/) → **Add New Project**.
- Import repository, set Root Directory to `frontend`.
- Environment Variable:
  - `VITE_API_BASE_URL`: `https://attendora-api.up.railway.app/api`
- Update [`frontend/vercel.json`](file:///c:/Users/neete/OneDrive/ドキュメント/attendora/frontend/vercel.json) destination to your backend URL.
- Deploy. Vercel automatically configures global CDN caching and SSL.

---

## 🛡️ Option 4: Bare-Metal Ubuntu Server (Systemd + Uvicorn)

If deploying directly onto bare metal without Docker:

### 1. System Packages
```bash
sudo apt update && sudo apt install -y python3-pip python3-venv build-essential cmake libopenblas-dev liblapack-dev libx11-dev libgl1 libglib2.0-0 nginx postgresql postgresql-contrib
```

### 2. Backend Systemd Service
Create `/etc/systemd/system/attendora-backend.service`:
```ini
[Unit]
Description=ATTENDORA FastAPI Service
After=network.target postgresql.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/attendora/backend
Environment="PATH=/var/www/attendora/backend/venv/bin"
EnvironmentFile=/var/www/attendora/backend/.env
ExecStart=/var/www/attendora/backend/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4

Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable attendora-backend
sudo systemctl start attendora-backend
```

### 3. Frontend Build & Static Serving
```bash
cd /var/www/attendora/frontend
npm install
npm run build
sudo cp -r dist/* /var/www/html/
```

---

## 🔒 Production Security Checklist

| Item | Recommendation | Status |
|---|---|---|
| **JWT Secret** | Generate 32+ byte string (`openssl rand -hex 32`) | Set via `SECRET_KEY` |
| **CORS Origins** | Do NOT use `*` in production; list exact domain | Set via `ALLOWED_ORIGINS` |
| **Database Passwords** | Strong alphanumeric password (16+ chars) | Set via `POSTGRES_PASSWORD` |
| **HTTPS / SSL** | Mandatory for webcam & camera browser APIs | Provided via Nginx / Certbot |
| **Automated Backups** | Daily `pg_dump` cron job | Run `docker exec attendora-db pg_dump ...` |
| **Static Uploads** | Mounted persistent volume for `/app/uploads` | Configured in `docker-compose.yml` |

---

## 🔄 Useful Operational Commands

```bash
# Restart all containers
docker compose restart

# View real-time logs
docker compose logs -f backend

# Backup PostgreSQL database
docker compose exec postgres pg_dump -U postgres attendora > backup_$(date +%Y%m%d).sql

# Restore PostgreSQL database
cat backup.sql | docker compose exec -T postgres psql -U postgres attendora

# Update to latest code
git pull
docker compose up -d --build
```
