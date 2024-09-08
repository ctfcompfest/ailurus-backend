#!/bin/bash

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --creds-file)
            KEY_FILE="$2"
            shift 2
            ;;
        --project-id)
            PROJECT_ID="$2"
            shift 2
            ;;
        --prefix)
            INSTANCE_PREFIX="$2"
            shift 2
            ;;
        --zone)
            ZONE="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Check for required arguments
if [[ -z $KEY_FILE || -z $PROJECT_ID || -z $INSTANCE_PREFIX ]]; then
    echo "Usage: $0 --creds-file <file> --project-id <id> --prefix <prefix> [--zone <zone>]"
    exit 1
fi

# Set default value for zone if not provided
ZONE=${ZONE:-"us-central1"}

# Authenticate the service account
gcloud auth activate-service-account --key-file="$KEY_FILE" --quiet

# Delete Kubernetes engine cluster
gcloud beta container --project "$PROJECT_ID" clusters delete "${INSTANCE_PREFIX}-gke-cluster" --region "$ZONE" --quiet

# Delete storage bucket
gcloud storage buckets delete "gs://${INSTANCE_PREFIX}-image-assets" --project="$PROJECT_ID" --quiet

# Delete image repository
gcloud artifacts repositories delete "${INSTANCE_PREFIX}-image-artifact" --location="$ZONE" --project="$PROJECT_ID" --quiet

# Delete NAT gateway
gcloud beta compute routers nats delete "${INSTANCE_PREFIX}-nat" --router="${INSTANCE_PREFIX}-router" --region="$ZONE" --project="$PROJECT_ID" --quiet
gcloud compute routers delete "${INSTANCE_PREFIX}-router" --region="$ZONE" --project="$PROJECT_ID" --quiet

# Delete firewall rules
gcloud compute firewall-rules delete "${INSTANCE_PREFIX}-allow-custom" --project="$PROJECT_ID" --quiet
gcloud compute firewall-rules delete "${INSTANCE_PREFIX}-allow-ssh" --project="$PROJECT_ID" --quiet
gcloud compute firewall-rules delete "${INSTANCE_PREFIX}-allow-icmp" --project="$PROJECT_ID" --quiet

# Delete GCP network
gcloud beta compute networks delete "${INSTANCE_PREFIX}-network" --project="$PROJECT_ID" --quiet

echo "GCP resources cleanup completed."