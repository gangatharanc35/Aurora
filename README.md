
# 🌅 Aurora - Daily Creative Agent

[![AWS](https://img.shields.io/badge/AWS-Powered-orange)](https://aws.amazon.com)
[![Bedrock](https://img.shields.io/badge/Amazon%20Bedrock-Nova-blue)](https://aws.amazon.com/bedrock/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

> An autonomous AI agent that generates original poetry and artwork daily using Amazon Bedrock Nova models. No human intervention needed — Aurora creates while you sleep.

## 🎯 What is Aurora?

Aurora is a **fully autonomous creative agent** that wakes up every day at dawn, generates a themed poem and accompanying artwork, and publishes it to a static website. It evolves its artistic style over time by tracking past creations and adapting.

**The best tool is the one you never have to open.**

### Key Features
- 🎨 **Daily Art Generation** — Original artwork via Amazon Nova Canvas
- 📝 **Daily Poetry** — Themed poems via Amazon Nova Lite
- 🌿 **Season-Aware** — Themes adapt to time of year and day of week
- 📈 **Style Evolution** — Artistic style rotates and evolves over time
- 🌐 **Auto-Published** — Static website updates automatically
- ⏰ **Fully Autonomous** — Runs on schedule, zero manual intervention

## 🏗️ Architecture

EventBridge │────▶│ AWS Lambda │────▶│ Amazon Bedrock │ │ (Daily Cron) │ │ (Aurora Agent) │ │ (Nova Models) │ └─────────────────┘ └──────────────────┘ └─────────────────┘ │ ┌───────────┼───────────┐ ▼ ▼ ▼ ┌──────────┐ ┌──────────┐ ┌──────────┐ │ Amazon │ │ DynamoDB │ │ S3 │ │ S3 │ │ (History)│ │ (Website)│ │(Storage) │ └──────────┘ └──────────┘ └──────────┘


### AWS Services Used
| Service | Purpose |
|---------|---------|
| **Amazon Bedrock** | AI model inference (Nova Lite for text, Nova Canvas for images) |
| **AWS Lambda** | Serverless compute for the agent |
| **Amazon EventBridge** | Daily scheduling (cron trigger) |
| **Amazon S3** | Storage + static website hosting |
| **Amazon DynamoDB** | Creation history & style evolution tracking |
| **AWS SAM** | Infrastructure as Code |

## 🚀 Deployment

### Prerequisites
- AWS Account with [Free Tier](https://aws.amazon.com/free/) access
- [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html) installed
- [AWS CLI](https://aws.amazon.com/cli/) configured with credentials
- Amazon Bedrock model access enabled for Nova Lite and Nova Canvas

### Quick Deploy

```bash
# 1. Clone the repository
git clone https://github.com/gangatharanc35/AWS-Builder-.git
cd AWS-Builder-

# 2. Build the SAM application
sam build

# 3. Deploy (first time - guided)
sam deploy --guided

# 4. Test immediately (optional)
aws lambda invoke --function-name aurora-creative-agent output.json
cat output.json
