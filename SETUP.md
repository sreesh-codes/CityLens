# CityLens API Key Setup Guide

## Prerequisites
- Node.js 18+ and Python 3.11+
- Supabase account
- Cloudinary account
- OpenAI developer account (GPT-4 Vision access)

## 1. Supabase
1. Create a new Supabase project at https://supabase.com/dashboard.
2. In **Project Settings → API**, copy the **Project URL** (`NEXT_PUBLIC_SUPABASE_URL`, `SUPABASE_URL`).
3. In the same panel copy:
   - **anon public key** → `NEXT_PUBLIC_SUPABASE_ANON_KEY` (frontend)
   - **service_role key** → `SUPABASE_SERVICE_KEY` (backend, keep secret)
4. In **Project Settings → Database → Connection info**, copy the **Connection string** (URI) → `DATABASE_URL`.
5. Apply the SQL migration in `backend/db/migrations/0001_citylens_schema.sql` using Supabase SQL Editor.

## 2. Cloudinary
1. Register at https://cloudinary.com/.
2. In the dashboard, note your **Cloud Name**, **API Key**, and **API Secret**.
3. Populate both frontend (`NEXT_PUBLIC_CLOUDINARY_CLOUD_NAME`) and backend (`CLOUDINARY_*` variables).
4. (Optional) Create upload presets for unsigned uploads if the frontend needs direct uploads.

## 3. OpenAI
1. Visit https://platform.openai.com/account/api-keys.
2. Create a key with GPT-4 Vision access and store it in `OPENAI_API_KEY` (backend only).
3. Ensure billing is enabled; GPT-4 Vision requires approved access.

## 4. Environment Files
- Frontend: `cp frontend/.env.example frontend/.env.local` and fill the values.
- Backend: `cp backend/.env.example backend/.env` and fill the values.

## 5. Local Development
```bash
# Frontend
cd frontend && npm install && npm run dev

# Backend
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## 6. Verification Checklist
- Accessing `http://localhost:3000` loads the Next.js placeholder page.
- `http://localhost:8000/health` returns `{ "status": "ok" }`.
- Supabase tables exist (Users, Reports, etc.) and contain seed data.
- Cloudinary uploads succeed using your credentials.
- GPT-4 Vision endpoint can be called from the backend (test using stub).
