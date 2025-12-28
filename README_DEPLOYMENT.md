# 🚀 Churn Prediction API - Deployment Guide

Complete guide to deploy your AutoGluon churn prediction model as a production API.

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Local Development](#local-development)
3. [Docker Deployment](#docker-deployment)
4. [Testing the API](#testing-the-api)
5. [Production Deployment](#production-deployment)
6. [Monitoring](#monitoring)
7. [Troubleshooting](#troubleshooting)

---

## 🎯 Quick Start

### Prerequisites
- Python 3.10+
- Docker (optional, for containerization)
- Your trained AutoGluon model in `./autogluon_churn_model_hpo/`

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Run the API
```bash
python app.py
```

The API will be available at: **http://localhost:8000**

📖 **Interactive API Documentation**: http://localhost:8000/docs

---

## 💻 Local Development

### 1. Start the Development Server

```bash
# Method 1: Run with auto-reload (recommended for development)
python app.py

# Method 2: Run with uvicorn directly
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### 2. Test the Endpoints

**Health Check:**
```bash
curl http://localhost:8000/health
```

**Single Prediction:**
```bash
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "CUST_12345",
    "features": {
      "tenure_months": 24.5,
      "monthly_charges": 65.50,
      "total_charges": 1572.00,
      "service_calls": 2.0,
      "contract_duration": "Two-Year",
      "paperless_billing": 1.2,
      "tech_support": 0.9,
      "online_backup": 0.3,
      "payment_method": "Credit Card",
      "internet_service": 0.8,
      "streaming_tv": 0.5,
      "streaming_movies": 0.6,
      "device_protection": 0.2,
      "online_security": 0.7,
      "senior_citizen": 0.1
    },
    "threshold": 0.5
  }'
```

### 3. Run Automated Tests

```bash
python test_api.py
```

---

## 🐳 Docker Deployment

### Build the Docker Image

```bash
docker build -t churn-prediction-api:v1.0 .
```

### Run the Container

```bash
docker run -d \
  --name churn-api \
  -p 8000:8000 \
  -v $(pwd)/autogluon_churn_model_hpo:/app/autogluon_churn_model_hpo:ro \
  churn-prediction-api:v1.0
```

### Using Docker Compose (Recommended)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Check Container Health

```bash
docker ps
docker logs churn-api
```

---

## 🧪 Testing the API

### Manual Testing with cURL

**1. Health Check:**
```bash
curl http://localhost:8000/health
```

**2. Get Model Info:**
```bash
curl http://localhost:8000/model_info
```

**3. Single Prediction:**
```bash
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d @sample_customer.json
```

**4. Batch Prediction:**
```bash
curl -X POST "http://localhost:8000/predict_batch" \
  -H "Content-Type: application/json" \
  -d @sample_batch.json
```

### Automated Testing

```bash
# Run the test suite
python test_api.py

# Expected output:
# ✅ Health Check: PASSED
# ✅ Single Prediction: PASSED
# ✅ Batch Prediction: PASSED
# ✅ Model Info: PASSED
```

### Load Testing (Optional)

```bash
# Install locust
pip install locust

# Run load test
locust -f load_test.py --host=http://localhost:8000
```

---

## 🌐 Production Deployment

### Option 1: Cloud Platform (AWS, Azure, GCP)

#### AWS Elastic Beanstalk
```bash
# Install EB CLI
pip install awsebcli

# Initialize and deploy
eb init -p docker churn-prediction-api
eb create churn-api-prod
eb open
```

#### AWS ECS/Fargate
```bash
# Push to ECR
aws ecr create-repository --repository-name churn-prediction-api
docker tag churn-prediction-api:v1.0 <your-ecr-url>
docker push <your-ecr-url>

# Deploy to ECS (use AWS Console or CloudFormation)
```

#### Azure Container Instances
```bash
az container create \
  --resource-group myResourceGroup \
  --name churn-api \
  --image churn-prediction-api:v1.0 \
  --dns-name-label churn-api \
  --ports 8000
```

### Option 2: Kubernetes

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: churn-prediction-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: churn-api
  template:
    metadata:
      labels:
        app: churn-api
    spec:
      containers:
      - name: api
        image: churn-prediction-api:v1.0
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
```

Deploy:
```bash
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
```

### Option 3: Virtual Machine

```bash
# SSH into VM
ssh user@your-vm-ip

# Clone repository
git clone <your-repo>
cd AutoGluOn_End_to_End

# Install dependencies
pip install -r requirements.txt

# Run with production server
gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

### Production Checklist

- [ ] Set `reload=False` in production
- [ ] Use proper number of workers (2-4 per CPU core)
- [ ] Set up HTTPS/SSL
- [ ] Configure firewall rules
- [ ] Set up monitoring and logging
- [ ] Implement rate limiting
- [ ] Add authentication if needed
- [ ] Set up backup/restore for model
- [ ] Configure auto-scaling

---

## 📊 Monitoring

### Application Metrics

Monitor these endpoints:
- `/health` - API health status
- `/model_info` - Model version and performance

### Key Metrics to Track

1. **Performance Metrics:**
   - Request latency (p50, p95, p99)
   - Requests per second
   - Error rate

2. **Business Metrics:**
   - Predictions per day
   - High-risk predictions
   - Model accuracy on recent data

3. **System Metrics:**
   - CPU usage
   - Memory usage
   - Disk I/O

### Setting Up Monitoring

**Option 1: Prometheus + Grafana**
```bash
# Add prometheus client
pip install prometheus-client

# Expose metrics endpoint
# (Add to app.py)
```

**Option 2: Cloud Provider Monitoring**
- AWS CloudWatch
- Azure Monitor
- GCP Cloud Monitoring

### Logging

Logs are written to stdout by default. Configure log aggregation:

```bash
# View logs in Docker
docker logs churn-api -f

# Or with docker-compose
docker-compose logs -f churn-api
```

---

## 🔧 Troubleshooting

### Common Issues

**1. Model not loading:**
```
Error: Model not loaded. Please try again later.
```
**Solution:** Verify model path in `app.py` matches your model directory.

**2. Port already in use:**
```
Error: Address already in use
```
**Solution:**
```bash
# Find process using port 8000
lsof -i :8000  # Linux/Mac
netstat -ano | findstr :8000  # Windows

# Kill the process or use different port
uvicorn app:app --port 8001
```

**3. Memory errors:**
```
MemoryError: Unable to allocate array
```
**Solution:** Increase container/VM memory or reduce batch size.

**4. Slow predictions:**
**Solution:** 
- Use batch predictions for multiple customers
- Increase number of workers
- Use GPU if available

### Debug Mode

Enable detailed logging:
```python
# In app.py
logging.basicConfig(level=logging.DEBUG)
```

### Performance Tuning

```bash
# Increase workers
uvicorn app:app --workers 4

# Use Gunicorn for production
gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker
```

---

## 📞 Support & Next Steps

### Additional Resources

- **FastAPI Documentation:** https://fastapi.tiangolo.com/
- **AutoGluon Documentation:** https://auto.gluon.ai/
- **Docker Documentation:** https://docs.docker.com/

### Next Steps After Deployment

1. ✅ **Set up monitoring** (Prometheus, CloudWatch, etc.)
2. ✅ **Configure alerts** for API downtime or errors
3. ✅ **Implement rate limiting** to prevent abuse
4. ✅ **Add authentication** (API keys, OAuth)
5. ✅ **Set up CI/CD pipeline** for automatic deployments
6. ✅ **Create model versioning** system
7. ✅ **Build retraining pipeline** for model updates

---

## 🎉 Congratulations!

Your churn prediction API is now production-ready! 🚀

For questions or issues, refer to the main project documentation or open an issue.
