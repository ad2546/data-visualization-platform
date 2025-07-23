#!/bin/bash

# Deployment script for GCP

echo "Starting deployment to Google Cloud Platform..."

# Set project ID
PROJECT_ID="viz-tool-465716"

# Set default project
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "Enabling required APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable aiplatform.googleapis.com

# Build and deploy using Cloud Build
echo "Building and deploying with Cloud Build..."
gcloud builds submit --config cloudbuild.yaml .

echo "Deployment completed!"
echo "Your application should be available at:"
gcloud run services describe data-viz-app --region=us-central1 --format="value(status.url)"