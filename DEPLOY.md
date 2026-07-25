# PROS — Deploy to Production (FREE)

## Zero-Cost Stack
- **Frontend**: Vercel (free)
- **Backend**: Render (free tier)
- **Database**: Neon (free PostgreSQL, 512MB)
- **Cache**: Upstash (free Redis, 10K cmds/day)
- **Total**: $0/month

---

## Step 1: Create Free Accounts
1. https://vercel.com — sign up with GitHub
2. https://render.com — sign up with GitHub
3. https://neon.tech — sign up with GitHub
4. https://upstash.com — sign up with GitHub

## Step 2: Set Up Database (Neon)
1. Create a new project in Neon
2. Copy the connection string (it looks like `postgresql://...@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require`)
3. Save this as your `DATABASE_URL`

## Step 3: Set Up Redis (Upstash)
1. Create a new Redis database in Upstash
2. Copy the `REDIS_URL` from the connection details

## Step 4: Deploy Backend (Render)
1. Create a new **Web Service** on Render
2. Connect your GitHub repo
3. Settings:
   - **Name**: pros-backend
   - **Runtime**: Docker
   - **Dockerfile**: `backend/Dockerfile`
   - **Port**: 8000
4. Add Environment Variables:
   ```
   APP_NAME=PROS
   APP_ENV=production
   SECRET_KEY=<generate-random-64-chars>
   FRONTEND_URL=https://your-app.vercel.app
   DATABASE_URL=<your-neon-connection-string>
   REDIS_URL=<your-upstash-url>
   JWT_SECRET_KEY=<generate-random-64-chars>
   JWT_ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=15
   REFRESH_TOKEN_EXPIRE_DAYS=7
   LINKEDIN_CLIENT_ID=<your-linkedin-client-id>
   LINKEDIN_CLIENT_SECRET=<your-linkedin-client-secret>
   LINKEDIN_REDIRECT_URI=https://pros-backend.onrender.com/api/auth/callback/linkedin
   GOOGLE_CLIENT_ID=<your-google-client-id>
   GOOGLE_CLIENT_SECRET=<your-google-client-secret>
   GOOGLE_REDIRECT_URI=https://pros-backend.onrender.com/api/auth/callback/google
   DEFAULT_AI_PROVIDER=anthropic
   ANTHROPIC_API_KEY=<your-anthropic-api-key>
   OPENAI_API_KEY=<your-openai-api-key>
   ENCRYPTION_KEY=<generate-random-44-chars>
   ```
5. Deploy (first deploy takes ~2-3 min)

## Step 5: Deploy Frontend (Vercel)
1. Import your GitHub repo on Vercel
2. Settings:
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
3. Add Environment Variable:
   - `VITE_API_URL` = `https://pros-backend.onrender.com/api`
4. Deploy

## Step 6: Update Backend CORS
On Render, update `FRONTEND_URL` to your actual Vercel URL.

## Step 7: Configure OAuth Redirects
Update these in LinkedIn Developer Portal and Google Cloud Console:
- LinkedIn: `https://pros-backend.onrender.com/api/auth/callback/linkedin`
- Google: `https://pros-backend.onrender.com/api/auth/callback/google`

## Step 8: Run Database Migration
After first deploy, the database tables are auto-created on startup.
If you need to run the interests migration, it's also auto-run.

---

## Generate Secret Keys

Run this in Python to generate keys:
```python
import secrets
print("SECRET_KEY:", secrets.token_urlsafe(48))
print("JWT_SECRET_KEY:", secrets.token_urlsafe(48))
print("ENCRYPTION_KEY:", secrets.token_urlsafe(32))
```

## Chrome Extension
1. Update `extension/popup.js` and `extension/background.js`:
   - Replace the default API URL with your Render backend URL
2. Load in Chrome:
   - Go to `chrome://extensions`
   - Enable Developer Mode
   - Click "Load unpacked"
   - Select the `extension` folder

---

## Important Notes

### Render Free Tier
- Services **spin down after 15 min of inactivity**
- First request after idle takes ~30-60s to wake up
- This is fine for personal use
- Consider the $7/mo plan if this bothers you

### Neon Free Tier
- 512 MB storage
- 24/7 compute (no cold starts)
- More than enough for personal use

### Upstash Free Tier
- 10,000 commands/day
- 100 MB storage
- More than enough for personal use
