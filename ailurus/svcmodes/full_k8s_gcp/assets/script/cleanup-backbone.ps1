param (
    [Parameter(Mandatory=$true)]
    [string]$CredsFile,

    [Parameter(Mandatory=$true)]
    [string]$ProjectId,

    [Parameter(Mandatory=$true)]
    [string]$Prefix = "ailurus",

    [Parameter(Mandatory=$false)]
    [string]$Zone = "us-central1"
)

# Define variables
$KEY_FILE = $CredsFile
$PROJECT_ID = $ProjectId
$INSTANCE_PREFIX = $Prefix
$ZONE = $Zone

# Authenticate the service account
gcloud auth activate-service-account --key-file=$KEY_FILE

# Delete Kubernetes engine cluster
gcloud beta container --project $PROJECT_ID clusters delete "$INSTANCE_PREFIX-gke-cluster" --region "$ZONE" --quiet

# Delete storage bucket
gcloud storage buckets delete "gs://$INSTANCE_PREFIX-image-assets" --project=$PROJECT_ID --quiet

# Delete image repository
gcloud artifacts repositories delete "$INSTANCE_PREFIX-image-artifact" --location=$ZONE --project=$PROJECT_ID  --quiet

# Delete NAT gateway
gcloud beta compute routers nats delete "$INSTANCE_PREFIX-nat" --router="$INSTANCE_PREFIX-router" --region=$ZONE --project=$PROJECT_ID  --quiet
gcloud compute routers delete "$INSTANCE_PREFIX-router" --region $ZONE --project=$PROJECT_ID  --quiet

# Delete firewall
gcloud compute firewall-rules delete "$INSTANCE_PREFIX-allow-custom" --project=$PROJECT_ID --quiet
gcloud compute firewall-rules delete "$INSTANCE_PREFIX-allow-ssh" --project=$PROJECT_ID --quiet
gcloud compute firewall-rules delete "$INSTANCE_PREFIX-allow-icmp" --project=$PROJECT_ID --quiet

# Delete GCP network
gcloud beta compute networks delete "$INSTANCE_PREFIX-network" --project=$PROJECT_ID  --quiet

Write-Host "GCP resources cleanup completed."