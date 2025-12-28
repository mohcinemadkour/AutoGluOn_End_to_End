# Deploying Churn Prediction Dashboard to Render.com

This guide walks you through deploying the Streamlit dashboard to Render.com.

## Prerequisites

- GitHub account with this repository pushed
- Render.com account (free tier available)
- AutoGluon model files (will need to be uploaded separately or stored in cloud storage)

## Deployment Steps

### Option 1: Deploy via Render Dashboard (Recommended)

1. **Sign up/Login to Render**
   - Go to https://render.com
   - Sign up or log in with your GitHub account

2. **Create a New Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select the `AutoGluOn_End_to_End` repository

3. **Configure the Service**
   - **Name**: `churn-prediction-dashboard`
   - **Region**: Choose closest to your users
   - **Branch**: `main`
   - **Root Directory**: Leave empty (or specify if in subdirectory)
   - **Environment**: `Python 3`
   - **Build Command**: 
     ```bash
     pip install -r requirements.txt
     ```
   - **Start Command**:
     ```bash
     streamlit run dashboard.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true --server.enableCORS=false
     ```

4. **Environment Variables** (Optional)
   - Add any environment variables needed for your app
   - Example: `MODEL_PATH=/opt/render/project/src/autogluon_churn_model_hpo`

5. **Choose Plan**
   - Select "Free" plan for testing (spins down after inactivity)
   - Or choose a paid plan for production use

6. **Deploy**
   - Click "Create Web Service"
   - Render will automatically deploy your app
   - Wait for the build to complete (5-10 minutes)

### Option 2: Deploy via render.yaml (Blueprint)

1. **Push render.yaml to your repository** (already created)

2. **Create New Blueprint**
   - In Render dashboard, click "New +" → "Blueprint"
   - Connect your GitHub repository
   - Select the repository containing `render.yaml`
   - Render will automatically read the configuration

3. **Review and Deploy**
   - Review the services that will be created
   - Click "Apply" to deploy

## Important Notes

### Model Files

⚠️ **The AutoGluon model files are too large for GitHub and Render's free tier.**

You have several options:

#### Option A: Use Cloud Storage (Recommended for Production)
1. Upload model to AWS S3, Google Cloud Storage, or Azure Blob Storage
2. Add download script in startup:
   ```python
   # Add to dashboard.py before load_model()
   import boto3
   import os
   
   if not os.path.exists('./autogluon_churn_model_hpo'):
       s3 = boto3.client('s3')
       # Download model from S3
       s3.download_file('your-bucket', 'model.tar.gz', 'model.tar.gz')
       # Extract model
       import tarfile
       with tarfile.open('model.tar.gz', 'r:gz') as tar:
           tar.extractall('.')
   ```

#### Option B: Use Render Persistent Disk
1. In Render dashboard, add a Persistent Disk to your service
2. Upload model files to the disk (100GB free tier limit)
3. Update `MODEL_PATH` environment variable

#### Option C: Train Model on First Run (For Demo Only)
- Modify dashboard to train a small model on synthetic data if no model exists
- Not recommended for production

### Free Tier Limitations

- **Spin Down**: Services on free tier spin down after 15 minutes of inactivity
- **First Load**: May take 30-60 seconds to wake up
- **Build Time**: Limited to 15 minutes for free tier
- **Disk Space**: Limited persistent storage

### Health Checks

Render uses `/_stcore/health` for Streamlit health checks (already configured).

## Post-Deployment

1. **Access Your Dashboard**
   - Render will provide a URL like: `https://churn-dashboard-xxxx.onrender.com`
   - Click the URL to access your dashboard

2. **Monitor Logs**
   - Click "Logs" in Render dashboard to see application logs
   - Useful for debugging issues

3. **Custom Domain** (Optional)
   - In Render dashboard, go to "Settings" → "Custom Domain"
   - Add your domain and follow DNS instructions

## Troubleshooting

### Build Fails
- Check that `requirements.txt` is in the root directory
- Verify Python version compatibility (3.8-3.11)
- Check build logs for specific errors

### App Crashes on Start
- Check logs for errors
- Verify model path exists
- Ensure all required files are present

### Model Loading Issues
- Verify model files are accessible
- Check file permissions
- Ensure sufficient disk space

### Performance Issues
- Consider upgrading to a paid plan for more resources
- Optimize model size
- Implement caching with `@st.cache_resource`

## Alternative Deployment Options

If Render doesn't work for your needs, consider:

1. **Streamlit Cloud** (streamlit.io/cloud)
   - Free tier available
   - Direct integration with GitHub
   - Limited resources for large models

2. **Hugging Face Spaces**
   - Free hosting for ML apps
   - Good for demo purposes

3. **AWS EC2 / Azure VM / Google Compute**
   - Full control
   - Better for large models
   - More expensive

4. **Docker on Cloud Run / ECS / AKS**
   - Use the included Dockerfile
   - Better scalability
   - Pay per use

## Cost Estimation (Render)

- **Free Tier**: $0/month (with limitations)
- **Starter**: $7/month (750 hrs, no spin down)
- **Standard**: $25/month (better performance)
- **Persistent Disk**: $0.25/GB/month

## Security Considerations

1. **Environment Variables**: Store sensitive data in environment variables
2. **Authentication**: Add Streamlit authentication if needed
3. **HTTPS**: Render provides free SSL certificates
4. **Rate Limiting**: Implement if needed for public access

## Support

- Render Documentation: https://render.com/docs
- Streamlit Documentation: https://docs.streamlit.io
- GitHub Issues: Report issues in your repository
