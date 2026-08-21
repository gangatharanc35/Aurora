
#!/bin/bash
# Aurora Creative Agent - Quick Deploy Script
# Usage: chmod +x deploy.sh && ./deploy.sh

set -e

echo "🌅 Deploying Aurora - Daily Creative Agent..."
echo "============================================="

# Check prerequisites
command -v sam >/dev/null 2>&1 || { echo "❌ AWS SAM CLI is required. Install: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html"; exit 1; }
command -v aws >/dev/null 2>&1 || { echo "❌ AWS CLI is required. Install: https://aws.amazon.com/cli/"; exit 1; }

# Verify AWS credentials
echo "📋 Checking AWS credentials..."
aws sts get-caller-identity > /dev/null || { echo "❌ AWS credentials not configured. Run: aws configure"; exit 1; }

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION=$(aws configure get region || echo "us-east-1")

echo "✅ Account: $ACCOUNT_ID"
echo "✅ Region: $REGION"

# Build
echo ""
echo "🔨 Building SAM application..."
sam build

# Deploy
echo ""
echo "🚀 Deploying to AWS..."
sam deploy \
    --stack-name aurora-creative-agent \
    --capabilities CAPABILITY_IAM \
    --resolve-s3 \
    --region $REGION \
    --no-confirm-changeset \
    --parameter-overrides BucketNameParam=aurora-creative-agent

# Get outputs
echo ""
echo "============================================="
echo "✅ Deployment Complete!"
echo ""
WEBSITE_URL=$(aws cloudformation describe-stacks --stack-name aurora-creative-agent --query "Stacks[0].Outputs[?OutputKey=='WebsiteURL'].OutputValue" --output text)
echo "🌐 Website: $WEBSITE_URL"
echo ""

# Trigger first creation
echo "🎨 Triggering first creation..."
aws lambda invoke --function-name aurora-creative-agent --payload '{"source": "manual", "trigger": "first-run"}' /tmp/aurora-output.json > /dev/null 2>&1
echo "✅ First creation triggered! Check the website in ~30 seconds."
echo ""
echo "🌅 Aurora will now create autonomously every day at 6 AM UTC."
echo "   No further action needed. Enjoy!"

