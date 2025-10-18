# Testing Cosmic Teacher Skill

## Method 1: Developer Console Test Tab (Easiest)

1. Go to [Developer Console](https://developer.amazon.com/alexa/console/ask)
2. Open your "Cosmic Teacher" skill
3. Click on **Test** tab at the top
4. Change dropdown from "Off" to "Development"
5. Type or speak these commands:

**Launch the skill:**
- Type: `open cosmic teacher`
- Or: `öffne cosmic teacher` (German)

**Have a conversation:**
- Type: `tell me about space`
- Type: `I want to say hello`
- Type: `how are you`

**Test slots:**
- Type: `tell me what is your favorite game`
- Type: `I want to say I had a great day at school`

## Method 2: Real Alexa Device

If you have an Alexa device registered to the same Amazon account:

1. Make sure skill is enabled for testing (Test tab → Development)
2. Say to your device: 
   - "Alexa, open Cosmic Teacher"
   - "Alexa, ask Cosmic Teacher how are you"
   - "Alexa, tell Cosmic Teacher I had a cool day"

## Method 3: ASK CLI Simulate (Command Line)

Test directly from terminal:

```bash
# Launch skill
ask dialog --skill-id amzn1.ask.skill.14a88490-52f7-46be-98c8-91de261d569e --locale de-DE

# Or simulate a specific utterance
ask smapi simulate-skill \
  -s amzn1.ask.skill.14a88490-52f7-46be-98c8-91de261d569e \
  -l de-DE \
  --text "öffne cosmic teacher" \
  --stage development
```

## Expected Behavior

1. **On launch:** Should greet you and ask how you are
2. **On chat:** Should respond using OpenAI with contextual answers
3. **On help:** Should explain what the skill does
4. **On stop/cancel:** Should say goodbye

## Troubleshooting

### If skill doesn't respond:
```bash
# Check logs
ask smapi get-skill-status -s amzn1.ask.skill.14a88490-52f7-46be-98c8-91de261d569e
```

### View error logs:
- Go to Code tab → CloudWatch Logs link
- Check for Python errors or OpenAI API errors

### Common issues:
- **"There was a problem with the requested skill's response"**
  - OpenAI API key not set or invalid
  - Check CloudWatch logs for error details

- **"I don't know that one"**
  - Interaction model not built properly
  - Try rebuilding: Build tab → Build Model

- **Skill doesn't understand utterances**
  - Make sure you're using the right invocation phrase
  - German: "öffne cosmic teacher" or "öffne kosmischen Lehrer"
  - English: "open cosmic teacher" (if EN locale added)
