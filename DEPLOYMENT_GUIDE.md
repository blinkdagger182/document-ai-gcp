# Deployment Guide - Document AI Backend

## 🚀 Deployment Options

### Option 1: Google Cloud Run (Recommended)

#### Prerequisites
- Google Cloud account
- `gcloud` CLI installed
- Project with billing enabled

#### Step 1: Install gcloud CLI
```bash
# macOS
brew install google-cloud-sdk

# Linux
curl https://sdk.cloud.google.com | bash

# Initialize
gcloud init
```

#### Step 2: Configure Project
```bash
# Set project
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

#### Step 3: Deploy
```bash
# Deploy from source (automatic build)
gcloud run deploy document-ai-backend \
  --source . \
  --platform managed \
  --region us-central1 \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --max-instances 10 \
  --allow-unauthenticated

# Note: First deployment takes 5-10 minutes (building container)
```

#### Step 4: Get Service URL
```bash
gcloud run services describe document-ai-backend \
  --region us-central1 \
  --format 'value(status.url)'
```

#### Configuration Options

**Memory & CPU:**
```bash
# For high-volume production
--memory 4Gi --cpu 4

# For development/testing
--memory 1Gi --cpu 1
```

**Scaling:**
```bash
# Auto-scaling
--min-instances 0 --max-instances 10

# Always warm (no cold starts)
--min-instances 1 --max-instances 5
```

**Authentication:**
```bash
# Public access
--allow-unauthenticated

# Require authentication
--no-allow-unauthenticated
```

---

### Option 2: Docker (Any Platform)

#### Build Image
```bash
docker build -t document-ai-backend .
```

#### Run Locally
```bash
docker run -p 8080:8080 document-ai-backend
```

#### Push to Registry
```bash
# Docker Hub
docker tag document-ai-backend username/document-ai-backend
docker push username/document-ai-backend

# Google Container Registry
docker tag document-ai-backend gcr.io/PROJECT_ID/document-ai-backend
docker push gcr.io/PROJECT_ID/document-ai-backend
```

---

### Option 3: AWS ECS/Fargate

#### Prerequisites
- AWS account
- AWS CLI installed
- ECR repository created

#### Step 1: Push to ECR
```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# Build and push
docker build -t document-ai-backend .
docker tag document-ai-backend:latest \
  ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/document-ai-backend:latest
docker push ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/document-ai-backend:latest
```

#### Step 2: Create ECS Task Definition
```json
{
  "family": "document-ai-backend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "2048",
  "memory": "4096",
  "containerDefinitions": [
    {
      "name": "document-ai-backend",
      "image": "ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/document-ai-backend:latest",
      "portMappings": [
        {
          "containerPort": 8080,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "PORT",
          "value": "8080"
        }
      ]
    }
  ]
}
```

#### Step 3: Create Service
```bash
aws ecs create-service \
  --cluster your-cluster \
  --service-name document-ai-backend \
  --task-definition document-ai-backend \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"
```

---

### Option 4: Azure Container Instances

```bash
# Login
az login

# Create resource group
az group create --name document-ai-rg --location eastus

# Deploy container
az container create \
  --resource-group document-ai-rg \
  --name document-ai-backend \
  --image your-registry/document-ai-backend \
  --cpu 2 \
  --memory 4 \
  --ports 8080 \
  --dns-name-label document-ai-backend \
  --environment-variables PORT=8080
```

---

### Option 5: Kubernetes (Any Cloud)

#### deployment.yaml
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: document-ai-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: document-ai-backend
  template:
    metadata:
      labels:
        app: document-ai-backend
    spec:
      containers:
      - name: document-ai-backend
        image: your-registry/document-ai-backend:latest
        ports:
        - containerPort: 8080
        env:
        - name: PORT
          value: "8080"
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
---
apiVersion: v1
kind: Service
metadata:
  name: document-ai-backend
spec:
  type: LoadBalancer
  ports:
  - port: 80
    targetPort: 8080
  selector:
    app: document-ai-backend
```

#### Deploy
```bash
kubectl apply -f deployment.yaml
kubectl get services
```

---

### Option 6: Local Development

#### Using Python directly
```bash
# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn main:app --reload --port 8080

# Or with auto-reload
python main.py
```

#### Using Docker Compose
```yaml
# docker-compose.yml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8080:8080"
    environment:
      - PORT=8080
    volumes:
      - ./main.py:/app/main.py
```

```bash
docker-compose up
```

---

## 🔧 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `8080` | Server port |
| `WORKERS` | `1` | Number of worker processes |
| `LOG_LEVEL` | `info` | Logging level |

---

## 📊 Monitoring & Logging

### Google Cloud Run
```bash
# View logs
gcloud run services logs read document-ai-backend \
  --region us-central1 \
  --limit 50

# Monitor metrics
gcloud run services describe document-ai-backend \
  --region us-central1
```

### Docker Logs
```bash
docker logs -f container_id
```

### Health Check Endpoint
```bash
# Monitor health
curl https://your-api.com/health

# Set up monitoring (example with UptimeRobot, Pingdom, etc.)
```

---

## 🔒 Security Best Practices

### 1. Enable HTTPS
Cloud Run provides HTTPS by default. For other platforms:
```bash
# Use reverse proxy (nginx, Caddy)
# Or configure SSL certificates
```

### 2. Restrict CORS
Update `main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-app.com"],  # Specific origins
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)
```

### 3. Add Authentication
```python
from fastapi import Header, HTTPException

async def verify_token(authorization: str = Header(None)):
    if not authorization or authorization != "Bearer YOUR_SECRET":
        raise HTTPException(status_code=401, detail="Unauthorized")

@app.post("/ocr", dependencies=[Depends(verify_token)])
async def ocr_endpoint(...):
    ...
```

### 4. Rate Limiting
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/ocr")
@limiter.limit("10/minute")
async def ocr_endpoint(...):
    ...
```

---

## 💰 Cost Optimization

### Google Cloud Run Pricing
- **Free tier:** 2 million requests/month
- **CPU:** $0.00002400/vCPU-second
- **Memory:** $0.00000250/GiB-second
- **Requests:** $0.40/million

**Example monthly cost:**
- 100,000 requests
- 2 seconds average processing
- 2 vCPU, 2GB memory
- **~$5-10/month**

### Optimization Tips
1. Use `--min-instances 0` for low traffic
2. Optimize image size (reduce layers)
3. Cache OCR models in container
4. Use appropriate memory/CPU settings

---

## 🧪 Testing Deployment

```bash
# Test health
curl https://your-api.com/health

# Test OCR
curl -X POST https://your-api.com/ocr \
  -F "file=@test.pdf" \
  | jq .

# Load testing
ab -n 100 -c 10 https://your-api.com/health
```

---

## 🔄 CI/CD Pipeline

### GitHub Actions Example
```yaml
# .github/workflows/deploy.yml
name: Deploy to Cloud Run

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - uses: google-github-actions/setup-gcloud@v0
        with:
          service_account_key: ${{ secrets.GCP_SA_KEY }}
          project_id: ${{ secrets.GCP_PROJECT_ID }}
      
      - name: Deploy to Cloud Run
        run: |
          gcloud run deploy document-ai-backend \
            --source . \
            --platform managed \
            --region us-central1 \
            --memory 2Gi \
            --cpu 2 \
            --allow-unauthenticated
```

---

## 📝 Troubleshooting

### Issue: Cold start timeout
**Solution:** Increase timeout or use min-instances
```bash
gcloud run services update document-ai-backend \
  --timeout 300 \
  --min-instances 1
```

### Issue: Out of memory
**Solution:** Increase memory allocation
```bash
gcloud run services update document-ai-backend \
  --memory 4Gi
```

### Issue: Slow OCR processing
**Solution:** Increase CPU
```bash
gcloud run services update document-ai-backend \
  --cpu 4
```

---

## 📞 Support

For deployment issues:
1. Check logs first
2. Verify environment variables
3. Test locally with Docker
4. Check resource limits
5. Review API documentation

---

## ✅ Post-Deployment Checklist

- [ ] Health endpoint returns 200
- [ ] OCR endpoint processes test PDF
- [ ] Overlay endpoint generates filled PDF
- [ ] CORS configured correctly
- [ ] Monitoring/logging enabled
- [ ] Backup/disaster recovery plan
- [ ] Documentation updated with API URL
- [ ] React Native app configured with new URL
