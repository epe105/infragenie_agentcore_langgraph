#!/bin/bash
#
# AIOps Demo - Lightweight Infrastructure Cleanup
# Removes: S3, API Gateway, CloudWatch Dashboard
#

set -e

echo "=========================================="
echo "AIOps Demo - Infrastructure Cleanup"
echo "=========================================="
echo ""

# Check for config file
CONFIG_FILE="/tmp/aiops_infrastructure_config.json"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ Error: Configuration file not found!"
    echo "   Expected: $CONFIG_FILE"
    echo ""
    echo "If you deployed manually, please provide resource names:"
    read -p "Bucket Code name: " BUCKET_CODE
    read -p "Bucket Data name: " BUCKET_DATA
    read -p "API Gateway ID: " API_ID
    read -p "CloudWatch dashboard name: " DASHBOARD_NAME
else
    echo "Found configuration file: $CONFIG_FILE"
    BUCKET_CODE=$(jq -r '.resources.bucket_code' "$CONFIG_FILE")
    BUCKET_DATA=$(jq -r '.resources.bucket_data' "$CONFIG_FILE")
    API_ID=$(jq -r '.resources.api_gateway_id' "$CONFIG_FILE")
    DASHBOARD_NAME=$(jq -r '.resources.cloudwatch_dashboard' "$CONFIG_FILE")

    echo ""
    echo "Resources to delete:"
    echo "  • Code Bucket:       $BUCKET_CODE"
    echo "  • Data Bucket:       $BUCKET_DATA"
    echo "  • API Gateway:       $API_ID"
    echo "  • CloudWatch Dashboard: $DASHBOARD_NAME"
fi

echo ""
echo "⚠️  WARNING: This will delete ALL resources!"
echo ""
read -p "Are you sure you want to delete everything? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Cleanup cancelled."
    exit 0
fi

echo ""
echo "=========================================="
echo "Step 1/4: Delete CloudWatch Dashboard"
echo "=========================================="

if [ ! -z "$DASHBOARD_NAME" ] && [ "$DASHBOARD_NAME" != "null" ]; then
    echo "Deleting CloudWatch dashboard: $DASHBOARD_NAME"
    aws cloudwatch delete-dashboards --dashboard-names "$DASHBOARD_NAME" 2>/dev/null || echo "Dashboard not found or already deleted"
    echo "✅ CloudWatch dashboard deleted"
else
    echo "⚠️  No dashboard name provided, skipping"
fi

echo ""
echo "=========================================="
echo "Step 2/4: Delete API Gateway"
echo "=========================================="

if [ ! -z "$API_ID" ] && [ "$API_ID" != "null" ]; then
    echo "Deleting API Gateway: $API_ID"
    aws apigateway delete-rest-api --rest-api-id "$API_ID" 2>/dev/null || echo "API not found or already deleted"
    echo "✅ API Gateway deleted"
else
    echo "⚠️  No API Gateway ID provided, skipping"
fi

echo ""
echo "=========================================="
echo "Step 3/4: Delete S3 Buckets"
echo "=========================================="

# Delete code bucket
if [ ! -z "$BUCKET_CODE" ] && [ "$BUCKET_CODE" != "null" ]; then
    if aws s3 ls "s3://$BUCKET_CODE" >/dev/null 2>&1; then
        echo "Emptying code bucket: $BUCKET_CODE"
        aws s3 rm "s3://$BUCKET_CODE" --recursive 2>/dev/null || echo "Bucket was already empty"

        # Delete all versions
        echo "Deleting all versions..."
        aws s3api list-object-versions \
            --bucket "$BUCKET_CODE" \
            --output json \
            --query 'Versions[].{Key:Key,VersionId:VersionId}' 2>/dev/null | \
        jq -c '.[]' 2>/dev/null | \
        while read version; do
            key=$(echo "$version" | jq -r '.Key')
            versionId=$(echo "$version" | jq -r '.VersionId')
            aws s3api delete-object --bucket "$BUCKET_CODE" --key "$key" --version-id "$versionId" 2>/dev/null || true
        done

        echo "Deleting code bucket..."
        aws s3api delete-bucket --bucket "$BUCKET_CODE" 2>/dev/null || echo "Bucket deletion failed"
        echo "✅ Code bucket deleted"
    else
        echo "⚠️  Code bucket not found, skipping"
    fi
else
    echo "⚠️  No code bucket provided, skipping"
fi

# Delete data bucket
if [ ! -z "$BUCKET_DATA" ] && [ "$BUCKET_DATA" != "null" ]; then
    if aws s3 ls "s3://$BUCKET_DATA" >/dev/null 2>&1; then
        echo "Emptying data bucket: $BUCKET_DATA"
        aws s3 rm "s3://$BUCKET_DATA" --recursive 2>/dev/null || echo "Bucket was already empty"

        echo "Deleting data bucket..."
        aws s3api delete-bucket --bucket "$BUCKET_DATA" 2>/dev/null || echo "Bucket deletion failed"
        echo "✅ Data bucket deleted"
    else
        echo "⚠️  Data bucket not found, skipping"
    fi
else
    echo "⚠️  No data bucket provided, skipping"
fi

echo ""
echo "=========================================="
echo "Step 4/4: Remove Configuration File"
echo "=========================================="

if [ -f "$CONFIG_FILE" ]; then
    rm -f "$CONFIG_FILE"
    echo "✅ Configuration file removed"
fi

echo ""
echo "=========================================="
echo "Cleanup Complete! ✅"
echo "=========================================="
echo ""
echo "All AIOps demo infrastructure has been removed."
echo ""
