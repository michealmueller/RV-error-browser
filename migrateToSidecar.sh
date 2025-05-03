#!/bin/bash

# Check if required tools are installed
command -v az >/dev/null 2>&1 || { echo "Azure CLI is required but not installed. Aborting." >&2; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "Docker is required but not installed. Aborting." >&2; exit 1; }

# Function to display usage
usage() {
    echo "Usage: $0 -s <subscription-id> -w <webapp-name> -g <resource-group> -n <slot-name>"
    echo "Example: $0 -s 12345678-1234-1234-1234-123456789012 -w mywebapp -g myresourcegroup -n staging"
    exit 1
}

# Parse command line arguments
while getopts "s:w:g:n:" opt; do
    case $opt in
        s) subscription_id="$OPTARG" ;;
        w) webapp_name="$OPTARG" ;;
        g) resource_group="$OPTARG" ;;
        n) slot_name="$OPTARG" ;;
        *) usage ;;
    esac
done

# Validate required parameters
if [ -z "$subscription_id" ] || [ -z "$webapp_name" ] || [ -z "$resource_group" ] || [ -z "$slot_name" ]; then
    usage
fi

# Set subscription
echo "Setting Azure subscription..."
az account set --subscription "$subscription_id"

# Create deployment slot
echo "Creating deployment slot..."
az webapp deployment slot create --name "$webapp_name" --resource-group "$resource_group" --slot "$slot_name"

# Get Docker Compose configuration
echo "Retrieving Docker Compose configuration..."
compose_config=$(az webapp config show --name "$webapp_name" --resource-group "$resource_group" --query linuxFxVersion -o tsv)
base64_value=$(echo "$compose_config" | cut -d'|' -f2)

# Decode Docker Compose configuration
echo "Decoding Docker Compose configuration..."
compose_yaml=$(echo "$base64_value" | base64 -d)
echo "$compose_yaml" > docker-compose.yml

# Parse services from docker-compose.yml
echo "Parsing services from docker-compose.yml..."
services=$(docker-compose config --services)

# Configure each container as a sidecar
for service in $services; do
    echo "Configuring container for service: $service"
    
    # Extract image and port from docker-compose.yml
    image=$(docker-compose config | yq ".services.$service.image")
    port=$(docker-compose config | yq ".services.$service.ports[0]" | cut -d':' -f1)
    
    # Determine if this is the main service (first service)
    is_main="false"
    if [ "$service" = "$(echo "$services" | head -n1)" ]; then
        is_main="true"
    fi
    
    # Create sidecar container
    az rest --method PUT \
        --url "https://management.azure.com/subscriptions/$subscription_id/resourceGroups/$resource_group/providers/Microsoft.Web/sites/$webapp_name/sitecontainers/$service?api-version=2023-12-01" \
        --body "{\"name\":\"$service\", \"properties\":{\"image\":\"$image\", \"isMain\": $is_main, \"targetPort\": $port}}"
done

# Switch to Sidecar mode
echo "Switching to Sidecar mode..."
az webapp config set --name "$webapp_name" --resource-group "$resource_group" --linux-fx-version "sitecontainers"

# Restart deployment slot
echo "Restarting deployment slot..."
az webapp restart --name "$webapp_name" --resource-group "$resource_group" --slot "$slot_name"

echo "Migration completed successfully!"
echo "Please validate the deployment slot before swapping to production."
echo "To swap to production, run:"
echo "az webapp deployment slot swap --name $webapp_name --resource-group $resource_group --slot $slot_name --target-slot production"
