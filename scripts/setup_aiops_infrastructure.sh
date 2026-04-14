#!/bin/bash
#
# AIOps Demo - Lightweight Infrastructure Setup (Fast Version)
# API Gateway Mock + S3 (No Lambda, No OpenSearch)
# Target Account: 
#

set -e

echo "=========================================="
echo "AIOps Demo - Lightweight Infrastructure"
echo "=========================================="
echo ""

# Configuration
TARGET_ACCOUNT=""
REGION="us-east-1"
TIMESTAMP=$(date +%s)
PROJECT_NAME="aiops-demo"

# Resource names
BUCKET_CODE="${PROJECT_NAME}-code-${TIMESTAMP}"
BUCKET_DATA="${PROJECT_NAME}-data-${TIMESTAMP}"
API_NAME="${PROJECT_NAME}-api"

# Verify AWS account
echo "Checking AWS account..."
CURRENT_ACCOUNT=$(aws sts get-caller-identity --query Account --output text 2>/dev/null || echo "error")

if [ "$CURRENT_ACCOUNT" = "error" ]; then
    echo "❌ Error: Unable to determine AWS account. Check your AWS credentials."
    exit 1
fi

echo "Current AWS Account: $CURRENT_ACCOUNT"
echo "Target AWS Account:  $TARGET_ACCOUNT"
echo ""

if [ "$CURRENT_ACCOUNT" != "$TARGET_ACCOUNT" ]; then
    echo "⚠️  WARNING: You are NOT in the target account!"
    read -p "Continue anyway? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        echo "Exiting."
        exit 0
    fi
fi

echo ""
echo "Estimated time: 2-3 minutes"
echo "Estimated cost: ~\$5-10/month"
echo ""
read -p "Continue with deployment? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Deployment cancelled."
    exit 0
fi

echo ""
echo "=========================================="
echo "Step 1/4: Create S3 Buckets"
echo "=========================================="

echo "[1/2] Creating code bucket: $BUCKET_CODE"
aws s3api create-bucket --bucket "$BUCKET_CODE" --region "$REGION" 2>/dev/null || echo "Bucket exists"
aws s3api put-bucket-versioning --bucket "$BUCKET_CODE" --versioning-configuration Status=Enabled
aws s3api put-bucket-tagging --bucket "$BUCKET_CODE" --tagging "TagSet=[{Key=Project,Value=AIOps-Demo}]"
echo "✅ Code bucket ready"

echo "[2/2] Creating data bucket: $BUCKET_DATA"
aws s3api create-bucket --bucket "$BUCKET_DATA" --region "$REGION" 2>/dev/null || echo "Bucket exists"
aws s3api put-bucket-tagging --bucket "$BUCKET_DATA" --tagging "TagSet=[{Key=Project,Value=AIOps-Demo}]"
echo "✅ Data bucket ready"
echo ""

echo "=========================================="
echo "Step 2/4: Create API Gateway (Simple)"
echo "=========================================="

echo "[1/7] Creating REST API..."
API_ID=$(aws apigateway create-rest-api \
    --name "$API_NAME" \
    --description "AIOps Demo API" \
    --endpoint-configuration types=REGIONAL \
    --query 'id' \
    --output text 2>/dev/null || aws apigateway get-rest-apis --query "items[?name=='$API_NAME'].id | [0]" --output text)
echo "✅ API ID: $API_ID"

echo "[2/7] Getting root resource..."
ROOT_RESOURCE_ID=$(aws apigateway get-resources --rest-api-id "$API_ID" --query 'items[?path==`/`].id | [0]' --output text)
echo "✅ Root resource: $ROOT_RESOURCE_ID"

echo "[3/7] Creating /events resource..."
EVENTS_RESOURCE_ID=$(aws apigateway create-resource \
    --rest-api-id "$API_ID" \
    --parent-id "$ROOT_RESOURCE_ID" \
    --path-part "events" \
    --query 'id' \
    --output text 2>/dev/null || \
    aws apigateway get-resources --rest-api-id "$API_ID" --query "items[?pathPart=='events'].id | [0]" --output text)
echo "✅ Events resource: $EVENTS_RESOURCE_ID"

echo "[4/7] Creating POST method..."
aws apigateway put-method \
    --rest-api-id "$API_ID" \
    --resource-id "$EVENTS_RESOURCE_ID" \
    --http-method POST \
    --authorization-type NONE >/dev/null 2>&1 || echo "Method exists"
echo "✅ POST method created"

echo "[5/7] Creating MOCK integration..."
aws apigateway put-integration \
    --rest-api-id "$API_ID" \
    --resource-id "$EVENTS_RESOURCE_ID" \
    --http-method POST \
    --type MOCK \
    --request-templates '{"application/json":"{\"statusCode\":200}"}' >/dev/null 2>&1 || echo "Integration exists"
echo "✅ Mock integration created"

echo "[6/7] Creating method response..."
aws apigateway put-method-response \
    --rest-api-id "$API_ID" \
    --resource-id "$EVENTS_RESOURCE_ID" \
    --http-method POST \
    --status-code 200 >/dev/null 2>&1 || echo "Response exists"
echo "✅ Method response created"

echo "[7/7] Creating integration response (full demo data)..."
# Full demo response with detailed network correlation
cat > /tmp/api_response.json <<'JSONEOF'
{"application/json":"{\"correlation_id\":\"$context.requestId\",\"timestamp\":\"$context.requestTime\",\"root_cause\":\"Network packet loss on primary path\",\"affected_layers\":[\"L2\",\"L3\",\"L7\"],\"confidence\":0.92,\"recommendation\":\"Failover to backup network path and adjust QoS policies\",\"risk_score\":72,\"events\":[{\"timestamp\":\"2025-03-24T14:31:30Z\",\"source\":\"infrastructure-monitor\",\"layer\":\"L2\",\"metric\":\"interface_errors\",\"value\":450,\"severity\":\"medium\",\"device\":\"core-router-01\",\"details\":\"CRC errors on GigabitEthernet0/1\"},{\"timestamp\":\"2025-03-24T14:31:45Z\",\"source\":\"cisco-network-monitor\",\"layer\":\"L3\",\"metric\":\"packet_loss\",\"value\":12.5,\"severity\":\"high\",\"path\":\"primary-wan-link\",\"details\":\"Packet loss on primary path\"},{\"timestamp\":\"2025-03-24T14:31:48Z\",\"source\":\"cisco-network-monitor\",\"layer\":\"L3\",\"metric\":\"latency\",\"value\":250,\"severity\":\"high\",\"details\":\"Latency increased from 15ms to 250ms\"},{\"timestamp\":\"2025-03-24T14:32:15Z\",\"source\":\"apm-monitor\",\"layer\":\"L7\",\"metric\":\"http_errors\",\"value\":89,\"severity\":\"critical\",\"service\":\"customer-api\",\"details\":\"HTTP 503 Service Unavailable\"}],\"correlation_analysis\":{\"temporal_pattern\":\"L2 errors (14:31:30) → L3 packet loss (14:31:45) → L7 impact (14:32:15)\",\"layer_dependency\":\"Physical layer errors cascading to network and application layers\",\"confidence_factors\":[\"Sequential timing indicates causation\",\"Geographic correlation: same datacenter link\",\"Similar error spike patterns\"]},\"remediation_plan\":{\"action\":\"automated_failover\",\"steps\":[\"Switch traffic to backup network path\",\"Adjust QoS policies\",\"Update routing tables\",\"Monitor backup path\"],\"estimated_downtime\":\"15 seconds\",\"approval_required\":true,\"rollback_plan\":\"Revert to primary after hardware replacement\"},\"verification_metrics\":{\"before\":{\"packet_loss\":\"12.5%\",\"latency\":\"250ms\",\"http_errors_per_min\":89,\"affected_users\":1250},\"after\":{\"packet_loss\":\"0.2%\",\"latency\":\"15ms\",\"http_errors_per_min\":0,\"affected_users\":0}}}"}
JSONEOF

aws apigateway put-integration-response \
    --rest-api-id "$API_ID" \
    --resource-id "$EVENTS_RESOURCE_ID" \
    --http-method POST \
    --status-code 200 \
    --response-templates file:///tmp/api_response.json >/dev/null 2>&1 || echo "Integration response exists"
rm -f /tmp/api_response.json
echo "✅ Integration response created (full demo quality)"

echo "[DEPLOY] Deploying to prod stage..."
aws apigateway create-deployment \
    --rest-api-id "$API_ID" \
    --stage-name prod \
    --description "Production" >/dev/null 2>&1 || echo "Deployed"

API_URL="https://${API_ID}.execute-api.${REGION}.amazonaws.com/prod/events"
echo "✅ API Gateway deployed"
echo ""

echo "=========================================="
echo "Step 3/4: Configure CloudWatch"
echo "=========================================="

DASHBOARD_JSON=$(cat <<EOF
{"widgets":[{"type":"metric","properties":{"metrics":[["AWS/ApiGateway","Count"]],"period":300,"stat":"Sum","region":"$REGION","title":"API Requests"}}]}
EOF
)

aws cloudwatch put-dashboard \
    --dashboard-name "${PROJECT_NAME}-dashboard" \
    --dashboard-body "$DASHBOARD_JSON" >/dev/null 2>&1
echo "✅ CloudWatch dashboard created"
echo ""

echo "=========================================="
echo "Step 4/4: Save Configuration"
echo "=========================================="

CONFIG_FILE="/tmp/aiops_infrastructure_config.json"
cat > "$CONFIG_FILE" <<EOF
{
  "project": "aiops-demo",
  "account": "$CURRENT_ACCOUNT",
  "region": "$REGION",
  "created_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "architecture": "lightweight",
  "resources": {
    "bucket_code": "$BUCKET_CODE",
    "bucket_data": "$BUCKET_DATA",
    "api_gateway_id": "$API_ID",
    "api_gateway_url": "$API_URL",
    "cloudwatch_dashboard": "${PROJECT_NAME}-dashboard"
  }
}
EOF

echo "✅ Configuration saved"
echo ""

echo "=========================================="
echo "Setup Complete! 🎉"
echo "=========================================="
echo ""
echo "Resources:"
echo "  • Code Bucket:  s3://$BUCKET_CODE"
echo "  • Data Bucket:  s3://$BUCKET_DATA"
echo "  • API Gateway:  $API_URL"
echo ""
echo "Test the API:"
echo "  curl -X POST $API_URL -H 'Content-Type: application/json' -d '{\"test\":true}'"
echo ""
echo "Cleanup:"
echo "  ./cleanup_aiops_infrastructure.sh"
echo ""
