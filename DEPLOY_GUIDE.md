# Quick Deploy to Render.com

## Step-by-Step Deployment Guide

### 1. Sign Up for Render.com
Go to https://render.com and sign up with your GitHub account.

### 2. Create New Web Service

1. Click **"New +"** button → **"Web Service"**
2. Click **"Connect GitHub"** (if not already connected)
3. Find and select your `AutoGluOn_End_to_End` repository
4. Click **"Connect"**

### 3. Configure Service

Fill in the following settings:

| Setting | Value |
|---------|-------|
| **Name** | `churn-prediction-dashboard` |
| **Region** | `Ohio (US East)` (or closest to you) |
| **Branch** | `main` |
| **Root Directory** | (leave empty) |
| **Environment** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `streamlit run dashboard.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true` |

### 4. Choose Instance Type

- **Free**: For testing (spins down after 15 min of inactivity, restarts on access)
- **Starter ($7/mo)**: For low-traffic production (always on)
- **Standard ($25/mo)**: For higher traffic (better performance)

Click **"Free"** for now.

### 5. Deploy

Click **"Create Web Service"** button at the bottom.

Render will:
- Clone your GitHub repository
- Install dependencies from requirements.txt
- Start the Streamlit dashboard

**This will take 5-10 minutes.**

### 6. Monitor Deployment

Watch the **Logs** tab to see:
- ✅ Build progress
- ✅ Installation of packages
- ✅ Application startup

### 7. Access Your Dashboard

Once deployed, you'll see:
- **URL**: `https://churn-prediction-dashboard-xxxx.onrender.com`
- Click the URL to access your dashboard!

---

## ⚠️ Important: Model Files

**The dashboard won't work immediately because model files are too large for GitHub.**

### Quick Fix for Testing (Synthetic Data)

The dashboard will automatically generate synthetic customer data if no real data is available. This works out of the box for demo purposes!

### For Production (Real Model)

You need to upload the model files. Choose one option:

#### Option A: Use Render Persistent Disk (Simplest)

1. In your Render service, go to **"Disks"** tab
2. Click **"Add Disk"**
3. Set:
   - **Name**: `model-storage`
   - **Mount Path**: `/data`
   - **Size**: `10 GB` (adjust based on model size)
4. Click **"Create Disk"**
5. Upload model files manually:
   ```bash
   # On your local machine
   tar -czf model.tar.gz autogluon_churn_model_hpo/
   
   # Use render's shell or SCP to upload
   ```
6. Update dashboard.py to load from `/data/autogluon_churn_model_hpo`

#### Option B: Use Cloud Storage (AWS S3)

1. Upload model to S3:
   ```bash
   aws s3 cp autogluon_churn_model_hpo/ s3://your-bucket/models/ --recursive
   ```

2. Add environment variables in Render:
   - `MODEL_BUCKET`: `your-bucket-name`
   - `MODEL_KEY`: `models/autogluon_churn_model_hpo`
   - `AWS_ACCESS_KEY_ID`: Your AWS key
   - `AWS_SECRET_ACCESS_KEY`: Your AWS secret

3. Update `setup_render.py` to download from S3

---

## Testing Your Deployment

1. Visit your Render URL
2. You should see the dashboard load
3. If using synthetic data, you'll see 500 sample customers
4. Try the different tabs and filters

---

## Troubleshooting

### "Application Error" or "Service Unavailable"
- Check the **Logs** tab in Render dashboard
- Look for Python errors or missing dependencies

### Dashboard loads but shows model error
- Model files are not accessible
- Check the path in dashboard.py matches your deployment
- Use synthetic data mode for testing

### Very slow loading
- Free tier spins down after inactivity
- First load after idle can take 30-60 seconds
- Consider upgrading to Starter plan ($7/mo) for always-on

### Build fails
- Check requirements.txt is valid
- Verify Python version compatibility
- Look for package installation errors in logs

---

## Next Steps

### Custom Domain
1. Go to **Settings** → **Custom Domain**
2. Add your domain
3. Update DNS records as instructed

### Environment Variables
1. Go to **Environment** tab
2. Add any secrets or configuration
3. Restart service to apply

### Auto-Deploy
- Render automatically deploys when you push to `main` branch
- Disable in **Settings** if you want manual control

### Monitoring
- Check **Metrics** tab for resource usage
- Set up **Notifications** for deploy status

---

## Costs

| Plan | Monthly Cost | Features |
|------|-------------|----------|
| Free | $0 | Spins down after 15 min, 750 hrs/mo |
| Starter | $7 | Always on, better performance |
| Standard | $25 | More CPU/RAM, better for production |
| Persistent Disk | +$0.25/GB | For model storage |

**Estimated for this project:**
- Free tier: Good for demo/testing
- Starter + 10GB disk: ~$9.50/mo for production
- Standard + 10GB disk: ~$27.50/mo for high traffic

---

## Support & Resources

- **Render Docs**: https://render.com/docs/web-services
- **Streamlit Docs**: https://docs.streamlit.io/
- **GitHub Repo**: Your repository with all code
- **Detailed Guide**: See [README_RENDER_DEPLOYMENT.md](README_RENDER_DEPLOYMENT.md)

---

## ✅ Success Checklist

- [ ] Render account created
- [ ] GitHub repository connected
- [ ] Web service created and deployed
- [ ] Dashboard URL accessible
- [ ] Dashboard loads (with synthetic data)
- [ ] All tabs work correctly
- [ ] (Optional) Model files uploaded
- [ ] (Optional) Custom domain configured
- [ ] (Optional) Monitoring set up

---

**Need help?** Open an issue in the GitHub repository or check Render's documentation.
