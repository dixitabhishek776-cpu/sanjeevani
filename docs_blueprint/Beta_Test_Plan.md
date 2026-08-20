# Sanjeevani — Beta Test Plan

## Purpose
This is a structured plan for testing Sanjeevani with real people, once you're
ready for that step. It is NOT a substitute for clinical review — treat
this as validating that the *software* works as intended, not as
validating that the *safety logic is clinically sound*. Those are
different questions, and only a licensed professional can answer the
second one.

## Before you recruit anyone
- [ ] Clinical advisor has reviewed the Safety Agent's prompt and logic
- [ ] You have a real (even if small) reviewer queue staffed — someone
      is actually watching for High/Immediate alerts during the beta
- [ ] Testers are told clearly, in writing, that this is NOT a crisis
      service and NOT a replacement for therapy — this should be shown
      before they can send their first message
- [ ] You have a way to reach testers directly if something concerning
      comes up (this is a real safety requirement, not a formality)

## Who to recruit
- Start small: 5-10 people, not a public release
- Prioritize people who can give thoughtful feedback, not just "does it
  work" — classmates, friends comfortable giving honest critique
- Avoid recruiting anyone you know to be currently in a mental health
  crisis for this early stage — that's not what an unvalidated beta is for

## What to test

### 1. Functional walkthrough (does it work)
| Area | What to check |
|---|---|
| Registration/login | Can a new user sign up and log in without confusion? |
| Chat | Does the AI reply feel natural? Any broken/empty replies? |
| Mood tracking | Is logging mood quick? Does the timeline make sense? |
| Journal | Any friction writing/saving entries? |
| Privacy dashboard | Can testers find and understand the consent toggles? Does export actually produce a usable file? |
| Crisis resources | Is the link easy to find? Does it work without being logged in? |

### 2. Tone and trust (does it feel right)
Ask testers directly:
- Did any AI response feel judgmental, dismissive, or "off"?
- Did anything feel like it was pretending to be a therapist?
- Would you trust this with something you're actually going through?

### 3. Safety behavior (test carefully, with consent)
**Only do this with testers who explicitly opt in and understand what
they're testing.** Have them try a few pre-written, clearly fictional
"test messages" (not describing their real feelings) to see how the
system responds — e.g., a message with sadness/hopelessness language.
Never ask someone to describe real distress just to test the system.

Check:
- Does the resources banner appear when expected?
- Does the AI's tone stay supportive rather than clinical/cold?
- Does anything in the reply feel dismissive of what was flagged?

### 4. Edge cases testers naturally hit
- What happens if they close the app mid-conversation and come back?
- What happens on a slow/flaky connection?
- Do they try language other than English? (Known current gap — see below)

## Known limitations to tell testers upfront
- The AI safety classifier is not clinically validated yet
- The app currently only reliably recognizes crisis language in English
- Long-term memory, voice, and wearables are not yet built
- This is explicitly not a crisis service — testers should be reminded
  where to go for real support if they need it

## Feedback collection
- A short form (5-7 questions) after each session beats a long survey —
  people abandon long ones
- Ask for the specific moment something felt off, not just a rating
- Weekly check-in with testers for the first 2 weeks, not just an end survey

## Success criteria for this stage
This beta is successful if you learn:
- Whether the core experience feels trustworthy and usable
- Concrete UX friction points
- Any pipeline bugs under real (not simulated) usage

It is NOT meant to prove the safety system is ready for real crisis
situations — that determination still requires your clinical advisor,
not tester feedback.
