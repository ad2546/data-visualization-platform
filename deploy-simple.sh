#!/bin/bash

# Simple deployment script for GCP Cloud Run

echo "Starting simple deployment to Google Cloud Platform..."

# Set project ID
PROJECT_ID="viz-tool-465716"

# Set default project
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "Enabling required APIs..."
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable aiplatform.googleapis.com

# Build Docker image locally and push to Container Registry
echo "Building Docker image..."
docker build --platform linux/amd64 -t gcr.io/$PROJECT_ID/data-viz-app:latest .

echo "Pushing Docker image to Container Registry..."
docker push gcr.io/$PROJECT_ID/data-viz-app:latest

# Deploy to Cloud Run
echo "Deploying to Cloud Run..."
gcloud run deploy data-viz-app \
    --image gcr.io/$PROJECT_ID/data-viz-app:latest \
    --region us-central1 \
    --platform managed \
    --allow-unauthenticated \
    --set-env-vars GOOGLE_GENAI_USE_VERTEXAI=1,GOOGLE_CLOUD_PROJECT=$PROJECT_ID,GOOGLE_CLOUD_LOCATION=us-central1,STORAGE_BUCKET_NAME=data07122025,MAX_FILE_SIZE_MB=1024,MAX_DIRECT_PROCESSING_SIZE_MB=100,SESSION_CLEANUP_HOURS=24,LOG_LEVEL=INFO \
    --memory 8Gi \
    --cpu 2 \
    --max-instances 10 \
    --min-instances 1 \
    --timeout 900 \
    --concurrency 10

echo "Deployment completed!"
echo "Your application should be available at:"
gcloud run services describe data-viz-app --region=us-central1 --format="value(status.url)"