# AWS Lambda Deployment Guide

## Prerequisites

1. **AWS Account** - Create at https://aws.amazon.com
2. **AWS CLI configured** - With your credentials
3. **ASK CLI linked to AWS** - Via `ask configure`

## Step 1: Configure AWS CLI

```bash
# Install AWS CLI if needed
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Configure with your credentials
aws configure
# Enter:
# - AWS Access Key ID
# - AWS Secret Access Key
# - Default region: eu-west-1
# - Default output format: json
```

## Step 2: Link ASK CLI with AWS

```bash
ask configure
# Follow prompts to:
# 1. Sign in to Amazon Developer account
# 2. Link AWS credentials
```

## Step 3: Deploy the Skill

```bash
cd /home/vasya/prj/alexa-skills/alexa-chat-skill-cosmic-teacher

# Deploy everything (skill + Lambda)
ask deploy

# The CLI will:
# 1. Create Lambda function in eu-west-1
# 2. Upload your code
# 3. Set up proper permissions
# 4. Update skill endpoint
```

## Step 4: Set Environment Variable

After deployment, set the OpenAI API key:

```bash
# Get the Lambda function name from deployment output
FUNCTION_NAME="ask-custom-Cosmic-Teacher-default"

# Set environment variable
aws lambda update-function-configuration \
  --function-name $FUNCTION_NAME \
  --environment "Variables={OPENAI_API_KEY=sk-proj-your-key-here}" \
  --region eu-west-1
```

## Step 5: View Logs

```bash
# View recent logs
aws logs tail /aws/lambda/$FUNCTION_NAME --follow --region eu-west-1

# Or in AWS Console:
# https://console.aws.amazon.com/cloudwatch/home?region=eu-west-1#logsV2:log-groups
```

## Benefits over Alexa-Hosted

✅ **Full CloudWatch access** - See all logs and errors
✅ **More control** - Configure timeout, memory, environment variables
✅ **Better debugging** - Python stack traces, print statements
✅ **No deployment delays** - Faster iteration
✅ **Free tier** - 1M requests/month free forever

## Cost Estimate

**Free tier (first 12 months + permanent):**
- 1,000,000 requests per month
- 400,000 GB-seconds compute time

**After free tier:**
- ~$0.20 per 1 million requests
- ~$0.0000166667 per GB-second

**For personal use:** Likely $0-2/month (usually $0)

## Current Configuration

- **Runtime:** Python 3.12
- **Handler:** lambda_function.handler
- **Region:** eu-west-1
- **Memory:** 128 MB (default)
- **Timeout:** 3 seconds (default)

## Troubleshooting

**Permission errors:**
```bash
# ASK CLI needs IAM permissions to create Lambda
# Make sure your AWS user has: AWSLambdaFullAccess, IAMFullAccess
```

**Deployment fails:**
```bash
# Delete old skill first if switching from hosted
ask smapi delete-skill -s amzn1.ask.skill.14a88490-52f7-46be-98c8-91de261d569e

# Then deploy fresh
ask deploy
```

**View deployment status:**
```bash
ask smapi get-skill-status -s <SKILL_ID>
```
