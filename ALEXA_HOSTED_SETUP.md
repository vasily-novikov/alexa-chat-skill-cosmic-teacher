# Alexa-Hosted Skill Setup Instructions

Since Alexa-hosted skills must be created through the Alexa Developer Console, follow these steps:

## Option 1: Create via Developer Console (Recommended)

1. **Go to Alexa Developer Console**:
   - Visit: https://developer.amazon.com/alexa/console/ask
   - Click "Create Skill"

2. **Configure the skill**:
   - Skill name: "Cosmic Teacher"
   - Primary locale: English (US)
   - Choose model: Custom
   - Hosting: **Alexa-hosted (Python)**
   - Click "Create skill"

3. **Choose a template**:
   - Select "Start from Scratch"
   - Click "Continue with template"

4. **After the skill is created**:
   - Note the Skill ID (shown in the URL)
   - Go to "Code" tab in the console
   - You'll see a Git repository URL

5. **Clone and update the hosted skill**:
   ```bash
   # Clone the Alexa-hosted Git repository
   ask init --hosted-skill-id <YOUR_SKILL_ID>
   
   # Or manually:
   git clone <ALEXA_GIT_URL> cosmic-teacher-hosted
   cd cosmic-teacher-hosted
   
   # Copy files from this project
   cp -r /home/vasya/prj/alexa-skills/alexa-chat-skill-cosmic-teacher/lambda/* lambda/
   cp -r /home/vasya/prj/alexa-skills/alexa-chat-skill-cosmic-teacher/skill-package/interactionModels skill-package/
   cp /home/vasya/prj/alexa-skills/alexa-chat-skill-cosmic-teacher/skill-package/skill.json skill-package/
   
   # Commit and push
   git add .
   git commit -m "Deploy Cosmic Teacher skill"
   git push origin master
   ```

6. **Set environment variable**:
   - In Developer Console → Code tab → Environment variables
   - Add: `OPENAI_API_KEY` = your OpenAI API key

## Option 2: Use AWS Lambda (Small Cost)

If you prefer to avoid the Alexa-hosted limitations and are okay with minimal AWS charges:

```bash
# Revert to Lambda deployer
cd /home/vasya/prj/alexa-skills/alexa-chat-skill-cosmic-teacher

# Configure AWS credentials
ask configure

# Deploy
ask deploy
```

AWS Lambda free tier includes:
- 1 million requests/month
- 400,000 GB-seconds compute time/month
- For personal use, likely stays free

## Current Project Status

- ✅ Skill metadata configured
- ✅ Interaction models fixed (removed invalid utterance)
- ✅ Lambda code ready
- ❌ Needs deployment target (Alexa-hosted OR AWS Lambda)

## Files Ready for Deployment

- `lambda/lambda_function.py` - Main skill handler
- `lambda/requirements.txt` - Dependencies (ask-sdk-core, requests)
- `skill-package/skill.json` - Skill manifest
- `skill-package/interactionModels/custom/en-US.json` - English interaction model
- `skill-package/interactionModels/custom/de-DE.json` - German interaction model
