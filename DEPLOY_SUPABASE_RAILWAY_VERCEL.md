# Step-by-Step Deployment: Supabase + Railway + Vercel

This guide walks you through deploying **ATTENDORA** across three best-in-class cloud platforms:
- **Database:** [Supabase](https://supabase.com/) (Managed PostgreSQL with pooling)
- **Backend API & Vision AI:** [Railway](https://railway.app/) (Containerized FastAPI with OpenCV & dlib)
- **Frontend SaaS Client:** [Vercel](https://vercel.com/) (High-speed Edge CDN for React + Vite)

---

## 📋 Architecture Flow

```
┌─────────────────────────┐          REST / WebSockets          ┌───────────────────────────────────┐
│     VERCEL (Frontend)   │ ──────────────────────────────────> │        RAILWAY (Backend)          │
│   https://attendora.app │                                     │ https://attendora.up.railway.app  │
└─────────────────────────┘                                     └───────────────────────────────────┘
                                                                                  │
                                                                                  │ Async SQL Connection
                                                                                  ▼
                                                                ┌───────────────────────────────────┐
                                                                │       SUPABASE (PostgreSQL)       │
                                                                │  db.project-ref.supabase.co:5432  │
                                                                └───────────────────────────────────┘
```

---

## 🗄️ PART 1: Database Setup on Supabase

### 1.1 Create a Supabase Project
1. Go to [database.new](https://database.new) (or log in to [Supabase](https://supabase.com/)).
2. Click **New Project**.
3. Fill in:
   - **Name:** `attendora`
   - **Database Password:** Enter a strong password and **save it safely**.
   - **Region:** Choose a region close to your Railway deployment (e.g. `US East (N. Virginia)`).
4. Click **Create new project** and wait ~1 minute for provisioning.

### 1.2 Run the Database Schema & Seed Data
1. In the Supabase Dashboard, click on **SQL Editor** in the left sidebar.
2. Click **New query**.
3. Open [`supabase_schema.sql`](./supabase_schema.sql) from this repository, copy the entire SQL script, and paste it into the editor.
4. Click **Run** (green button).
5. All 19 tables (`organizations`, `users`, `people`, `attendance_records`, `face_profiles`, etc.), enums, and initial subscription plans will be created instantly.

### 1.3 Get your Database Connection String
1. Go to **Project Settings** (gear icon at the bottom left) → **Database**.
2. Scroll to the **Connection parameters** / **Connection string** section.
3. Select **URI** mode:
   - **Session mode (Port 5432):**
     ```text
     postgresql://postgres.[YOUR-PROJECT-REF]:[YOUR-PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres
     ```
   - *Or Direct connection:*
     ```text
     postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres
     ```
4. Copy this URI. Our backend code in `app/core/database.py` automatically normalizes it, converts `postgresql://` to `postgresql+asyncpg://`, configures SSL, and tunes PgBouncer pooler arguments automatically!

---

## 🚂 PART 2: Backend Deployment on Railway

### 2.1 Push Code to GitHub
Ensure your `attendora` repository is pushed to GitHub:
```bash
git init
git add .
git commit -m "feat: complete attendora saas platform"
git branch -M main
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/attendora.git
git push -u origin main
```

### 2.2 Create Railway Project
1. Log in to [Railway.app](https://railway.app/).
2. Click **New Project** → **Deploy from GitHub repo**.
3. Select your `attendora` repository.
4. If prompted to select a directory or if Railway detects multiple directories:
   - Click on the created service card → Go to **Settings** tab.
   - Under **General** → **Root Directory**, set to: `/backend`
   - Under **Build** → Railway automatically detects [`backend/Dockerfile`](./backend/Dockerfile) and [`backend/railway.json`](./backend/railway.json).

### 2.3 Set Backend Environment Variables
In Railway, click the service → Go to the **Variables** tab and add the following keys:

| Variable Name | Value | Note |
|---|---|---|
| `DATABASE_URL` | `postgresql://postgres.[REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres` | Your Supabase URI from Part 1 |
| `SECRET_KEY` | *(Generate a 32+ char random string or use: `openssl rand -hex 32`)* | JWT signing secret |
| `ALLOWED_ORIGINS` | `*` *(or your Vercel URL once generated)* | CORS allowed list |
| `DEBUG` | `false` | Production flag |
| `APP_NAME` | `ATTENDORA` | Application title |
| `SUPER_ADMIN_EMAIL` | `admin@attendora.com` | Primary admin account |
| `SUPER_ADMIN_PASSWORD` | `Admin@12345` | Primary admin password |

### 2.4 Generate Public Domain
1. In the service **Settings** tab, scroll to **Networking** → **Public Networking**.
2. Click **Generate Domain**.
3. Railway will generate a public HTTPS URL (e.g., `https://attendora-production.up.railway.app`).
4. Test it by opening in your browser:
   - `https://attendora-production.up.railway.app/health` (should return `{"status": "healthy", ...}`)
   - `https://attendora-production.up.railway.app/docs` (interactive Swagger UI)

---

## ▲ PART 3: Frontend Deployment on Vercel

### 3.1 Import Project on Vercel
1. Log in to [Vercel.com](https://vercel.com/).
2. Click **Add New…** → **Project**.
3. Select your `attendora` GitHub repository.

### 3.2 Configure Build & Output
1. Under **Project Name**, enter `attendora` (or custom name).
2. Under **Framework Preset**, select **Vite**.
3. Under **Root Directory**, click **Edit** and select: `frontend`
4. Expand **Environment Variables** and add:

| Key | Value |
|---|---|
| `VITE_API_BASE_URL` | `https://attendora-production.up.railway.app/api` |

*(Replace with your actual Railway domain from Part 2)*

5. Click **Deploy**.

Vercel will install dependencies, compile the TypeScript code, package the assets, and deploy globally across Edge CDN networks in ~60 seconds.

---

## 🔗 PART 4: Final Connection & CORS Lock

1. Once Vercel finishes deploying, copy your public Vercel URL (e.g. `https://attendora.vercel.app`).
2. Go back to **Railway** → your Backend service → **Variables**.
3. Update `ALLOWED_ORIGINS`:
   ```text
   https://attendora.vercel.app,http://localhost:5173
   ```
4. Railway will automatically redeploy with the updated CORS policy in 10 seconds.

---

## 🎯 Verification & Testing

1. Open your Vercel URL: `https://attendora.vercel.app`.
2. The **Attendora Landing Page** will render with the live AI Scanner HUD.
3. Click **Log In** and enter default Super Admin credentials:
   - **Email:** `admin@attendora.com`
   - **Password:** `Admin@12345`
4. You will be redirected to the **Dashboard Overview**.
5. Test the modules:
   - **Members:** Add a new employee in the People directory.
   - **Face Enrollment:** Test the webcam capture with oval framing guide.
   - **Live Recognition:** Turn on the camera feed to test touchless verification.
