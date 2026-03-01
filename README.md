# mem_biosensors_front_back

## 🚀 Deploy to Cloudflare Pages

### Prerequisites
- A [Cloudflare](https://cloudflare.com) account (free tier is sufficient)
- This repository pushed to GitHub

### Steps

1. **Push your code to GitHub**
   ```bash
   git push origin main
   ```

2. **Connect the repo in Cloudflare Pages**
   - Go to **Cloudflare Dashboard → Pages → Create a project**
   - Select **Connect to Git** and authorise GitHub
   - Choose this repository

3. **Configure the build settings**

   | Setting | Value |
   |---|---|
   | Build command | `bash build.sh` |
   | Build output directory | `dist` |
   | Root directory | *(leave blank)* |

4. **Environment variables** *(optional)*

   | Variable | Example value |
   |---|---|
   | `NODE_VERSION` | `20` |
   | `PYTHON_VERSION` | `3.12` |

5. **Save and deploy** — Cloudflare will run `build.sh`, which:
   - Builds the Next.js frontend into `dist/` via `npm run build`
   - Copies the FastAPI backend into `dist/api/`
   - Installs Python dependencies into `dist/api/`

### Local development

```bash
# Frontend (http://localhost:3000)
cd frontend && npm install && npm run dev

# Backend (http://localhost:8000)
cd backend && pip install -r requirements.txt && uvicorn main:app --reload
```

### Build locally (same as CI)

```bash
bash build.sh
```

The output is placed in the `dist/` directory. Open `dist/index.html` in a browser or serve it with any static file server.
