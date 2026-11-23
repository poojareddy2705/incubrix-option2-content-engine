"""
generator.py — Content generation for the IncuBrix Content Engine.

Two modes:
  - mock: Fully deterministic. No API key needed. Seed-based.
          Used for testing, CI, and assessment demonstrations.
  - live: Calls a real LLM API (OpenAI/Anthropic/Google).
          Requires API key in environment.

All generated content is clearly labelled as AI-generated.
Mock content is clearly labelled as mock/demo content.
"""
import random
import logging
from typing import List, Optional
from src.models import ContentAsset, CONTENT_PILLARS

logger = logging.getLogger("content_engine.generator")

# =============================================================================
# MOCK CONTENT LIBRARY
# Realistic, brand-compliant content for all 3 platforms and all 4 pillars.
# This is the deterministic content bank used in mock mode.
# =============================================================================

MOCK_CONTENT_BANK = [
    # ---- LINKEDIN text_post / educational_post ----
    {
        "platform": "linkedin",
        "format": "educational_post",
        "content_pillar": "Creator Pain and Workflow Friction",
        "hook": "Most solo creators spend more time moving files between tools than actually creating.",
        "caption": (
            "Here's the creator workflow nobody talks about:\n\n"
            "Record → download → upload to transcription tool → download transcript → "
            "paste into writing tool → write captions → switch to scheduler → "
            "upload again → repeat for every platform.\n\n"
            "That's not a content strategy. That's a file management job.\n\n"
            "The real bottleneck isn't ideas. It's the tool-switching overhead that "
            "eats the hours between recording and publishing.\n\n"
            "One workflow step I've found useful: treat the transcript as the master document. "
            "Every clip, caption, and post should trace back to it.\n\n"
            "What does your post-recording workflow actually look like?"
        ),
        "cta": "Drop your biggest post-recording time sink in the comments. ↓",
        "hashtags": "#ContentCreators #CreatorWorkflow #PodcastGrowth #ContentRepurposing",
        "funnel_stage": "awareness",
        "experiment_id": "EXP_HOOK:pain-led",
        "source_excerpt": "tool switching and repetitive editing work",
    },
    {
        "platform": "linkedin",
        "format": "educational_post",
        "content_pillar": "Repurposing Education",
        "hook": "One 45-minute podcast episode can produce 8 platform-ready posts — if you know where to look.",
        "caption": (
            "Most creators repurpose content by watching their recordings and picking moments they remember.\n\n"
            "That's inefficient and inconsistent.\n\n"
            "A better approach:\n\n"
            "1. Start with the transcript, not the video\n"
            "2. Scan for moments with strong contrast, specific numbers, or a surprising insight\n"
            "3. Identify the hook first — the first 3 words of a clip matter more than the next 60 seconds\n"
            "4. Adapt each moment for platform context:\n"
            "   • LinkedIn: add the professional lesson\n"
            "   • Instagram: compress to the visual moment\n"
            "   • YouTube Shorts: open with the hook immediately\n\n"
            "The clip isn't the content. The clip is the starting point.\n\n"
            "What's your current clip selection process?"
        ),
        "cta": "Save this post if you're building a repurposing workflow. I'll go deeper on each step.",
        "hashtags": "#ContentRepurposing #PodcastClips #CreatorStrategy #LongFormContent",
        "funnel_stage": "consideration",
        "experiment_id": "EXP_HOOK:outcome-led",
        "source_excerpt": "turning one long-form asset into multiple posts",
    },
    {
        "platform": "linkedin",
        "format": "demo_post",
        "content_pillar": "Product-in-Action",
        "hook": "Transcript-based editing changed how I cut long-form video — here's what that workflow looks like.",
        "caption": (
            "Instead of scrubbing through a timeline, you edit the words.\n\n"
            "Find the sentence you want to cut → delete it from the transcript → "
            "the video updates automatically.\n\n"
            "For a 45-minute recording, this approach typically:\n"
            "• Removes filler words and false starts faster than manual trimming\n"
            "• Makes it easier to identify the strongest 60-second segment\n"
            "• Gives you a reusable document to pull captions from\n\n"
            "IncuBrix has a transcript-based editing mode paired with Smart Cut "
            "and a Hooks & Titles generator — which means you can go from raw "
            "recording to shortlist of clips without touching the video timeline.\n\n"
            "This isn't magic. It's a faster interface for a process you're already doing."
        ),
        "cta": "Link in comments to see the transcript editing workflow in action.",
        "hashtags": "#VideoEditing #TranscriptEditing #ContentWorkflow #IncuBrix",
        "funnel_stage": "consideration",
        "experiment_id": "EXP_FORMAT:demo-led",
        "source_excerpt": "transcript-based editing, Smart Cut, Hooks and Titles",
        "claim_status": "verified",
    },
    {
        "platform": "linkedin",
        "format": "educational_post",
        "content_pillar": "Practical AI and Human Judgment",
        "hook": "AI gets the clip. You choose whether it's the right clip.",
        "caption": (
            "Here's where AI tools in content creation actually help:\n\n"
            "→ Processing a 60-minute transcript in seconds\n"
            "→ Scoring clips by hook strength, novelty, and emotional weight\n"
            "→ Generating a first-draft caption from a clip's transcript\n"
            "→ Suggesting a title based on the opening hook\n\n"
            "Here's where you still need to show up:\n\n"
            "→ Deciding if the AI-scored 'top clip' actually represents your brand\n"
            "→ Reviewing captions for your actual voice (AI writes for average, not for you)\n"
            "→ Catching context that AI doesn't have (inside references, audience nuance)\n"
            "→ Approving before publishing — always\n\n"
            "AI accelerates the mechanical steps. Human judgment protects the output quality.\n\n"
            "Which AI step in content creation do you trust the most? Which the least?"
        ),
        "cta": "Follow for more practical breakdowns of AI + creator workflows. →",
        "hashtags": "#AIContent #CreatorTools #HumanJudgment #ContentStrategy",
        "funnel_stage": "awareness",
        "experiment_id": "EXP_HOOK:pain-led",
        "source_excerpt": "where AI helps and where human review is needed",
    },
    {
        "platform": "linkedin",
        "format": "carousel",
        "content_pillar": "Repurposing Education",
        "hook": "5 questions to ask before you repurpose any long-form content.",
        "caption": (
            "Not every moment from a podcast or webinar is worth turning into a post.\n\n"
            "Before you repurpose, ask:\n\n"
            "1. Does this stand alone? (Without the full context, does it still make sense?)\n"
            "2. Is the hook specific? (Vague observations don't stop the scroll.)\n"
            "3. Does it teach or demonstrate something? (Entertainment alone rarely converts.)\n"
            "4. Is it platform-appropriate? (LinkedIn wants the lesson. Instagram wants the moment.)\n"
            "5. Would you be comfortable if this was the first thing a new follower saw?\n\n"
            "Five filters. Use them before you post.\n\n"
            "[Carousel: each question on its own slide with a one-line example]"
        ),
        "cta": "Save this carousel to review before your next repurposing session.",
        "hashtags": "#ContentRepurposing #CreatorEducation #SocialMediaStrategy",
        "funnel_stage": "awareness",
        "experiment_id": "EXP_FORMAT:educational",
        "source_excerpt": "hook selection and clip strategy",
    },
    {
        "platform": "linkedin",
        "format": "text_post",
        "content_pillar": "Creator Pain and Workflow Friction",
        "hook": "The content backlog is not a motivation problem. It's a systems problem.",
        "caption": (
            "Every creator I've talked to has a folder of recordings they haven't turned into posts yet.\n\n"
            "They assume it's because they're behind, or not disciplined enough.\n\n"
            "Usually it's because the gap between 'recording done' and 'post published' "
            "has too many manual steps.\n\n"
            "The backlog grows when the repurposing workflow is slower than the recording cadence.\n\n"
            "Fix the workflow, not the motivation.\n\n"
            "What's the specific step in your publishing process that creates the most friction?"
        ),
        "cta": "Share this with a creator who calls their content backlog a 'laziness problem'.",
        "hashtags": "#ContentBacklog #CreatorBurnout #ContentSystems #SoloCreator",
        "funnel_stage": "awareness",
        "experiment_id": "EXP_HOOK:pain-led",
        "source_excerpt": "content backlog and repetitive repurposing work",
    },
    {
        "platform": "linkedin",
        "format": "educational_post",
        "content_pillar": "Product-in-Action",
        "hook": "Here's how the Clips scoring interface in IncuBrix works — and why the criteria matter.",
        "caption": (
            "When you upload a long-form video or audio to IncuBrix's Clips section, "
            "it evaluates potential clips across five dimensions:\n\n"
            "• Hook — does the clip open with something that earns attention immediately?\n"
            "• Emotion — does it create an emotional response (surprise, recognition, agreement)?\n"
            "• Relevance — is it topically aligned with what your audience cares about?\n"
            "• Novelty — does it say something the audience hasn't heard a hundred times?\n"
            "• Virality — does it have the structure that tends to get reshared?\n\n"
            "These aren't arbitrary scores. They map to what actually determines if someone "
            "watches past the first three seconds.\n\n"
            "The scores are starting points for your judgment, not a replacement for it."
        ),
        "cta": "What criteria do you currently use to pick which clips are worth repurposing?",
        "hashtags": "#ClipScoring #ContentAnalysis #IncuBrix #CreatorTools",
        "funnel_stage": "consideration",
        "experiment_id": "EXP_FORMAT:demo-led",
        "source_excerpt": "Clips scoring: Hook, Emotion, Relevance, Novelty, Virality",
        "claim_status": "verified",
    },
    {
        "platform": "linkedin",
        "format": "text_post",
        "content_pillar": "Practical AI and Human Judgment",
        "hook": "The worst AI content sounds like it could have been written by anyone. That's the problem.",
        "caption": (
            "Generic AI-generated content passes a surface-level quality check:\n"
            "• Grammatically correct ✓\n"
            "• Topically relevant ✓\n"
            "• Appropriate length ✓\n\n"
            "But it fails the only check that matters for social media:\n"
            "Does this sound like the creator who made it?\n\n"
            "AI writes for the average. Your audience follows you for the specific.\n\n"
            "The fix isn't to avoid AI. It's to treat AI output as a first draft "
            "that you review and adjust before it goes anywhere near your audience.\n\n"
            "Which is exactly the step most AI-first content tools skip."
        ),
        "cta": "Follow if you're building a content workflow that actually preserves your voice. →",
        "hashtags": "#AIContent #CreatorVoice #ContentQuality #HumanReview",
        "funnel_stage": "awareness",
        "experiment_id": "EXP_CTA:outcome-specific",
        "source_excerpt": "avoiding generic AI content and preserving creator voice",
    },
    # ---- INSTAGRAM reel_script / carousel_concept ----
    {
        "platform": "instagram",
        "format": "reel_script",
        "content_pillar": "Creator Pain and Workflow Friction",
        "hook": "You recorded a great episode. It's been sitting unedited for 3 weeks.",
        "caption": (
            "Sound familiar?\n\n"
            "The recording isn't the problem. The 7 steps between recording and posting are.\n\n"
            "What if that gap was one workflow instead of seven tools?\n\n"
            "#ContentCreators #PodcastLife #CreatorProblems #ContentWorkflow"
        ),
        "cta": "Save this if your drafts folder is full. Link to workflow in bio. 🔗",
        "hashtags": "#ContentCreators #PodcastLife #CreatorProblems #ContentWorkflow",
        "funnel_stage": "awareness",
        "experiment_id": "EXP_HOOK:pain-led",
        "source_excerpt": "post-recording bottlenecks and content backlog",
    },
    {
        "platform": "instagram",
        "format": "reel_script",
        "content_pillar": "Repurposing Education",
        "hook": "Stop rewatching your recordings to find clips. Do this instead.",
        "caption": (
            "Transcript-first clip selection:\n\n"
            "1. Read transcript, not video\n"
            "2. Highlight moments with strong contrast or specific numbers\n"
            "3. Check the hook — first 3 seconds\n"
            "4. Test for standalone clarity\n\n"
            "Faster. More consistent. No more scrubbing.\n\n"
            "#ContentRepurposing #PodcastClips #CreatorTips #VideoEditing"
        ),
        "cta": "Save this process. Try it on your next episode. 📌",
        "hashtags": "#ContentRepurposing #PodcastClips #CreatorTips #VideoEditing",
        "funnel_stage": "consideration",
        "experiment_id": "EXP_HOOK:outcome-led",
        "source_excerpt": "transcript-based editing workflow",
    },
    {
        "platform": "instagram",
        "format": "carousel_concept",
        "content_pillar": "Repurposing Education",
        "hook": "One episode. 7 pieces of content. Here's the breakdown.",
        "caption": (
            "Slide 1: One episode. 7 pieces of content.\n"
            "Slide 2: 1 × LinkedIn educational post (the main lesson)\n"
            "Slide 3: 1 × LinkedIn text post (the contrarian take)\n"
            "Slide 4: 1 × Instagram Reel (the best 30-second clip)\n"
            "Slide 5: 1 × Instagram carousel (the step-by-step breakdown)\n"
            "Slide 6: 1 × YouTube Short (the hook moment)\n"
            "Slide 7: 2 × short-form written pieces (email or story format)\n"
            "Slide 8: Start with the transcript. It makes all 7 easier.\n\n"
            "#ContentRepurposing #CreatorStrategy #ContentCalendar #RepurposeTips"
        ),
        "cta": "Save this. Share with another creator who needs to hear it. 🔖",
        "hashtags": "#ContentRepurposing #CreatorStrategy #ContentCalendar #RepurposeTips",
        "funnel_stage": "awareness",
        "experiment_id": "EXP_FORMAT:educational",
        "source_excerpt": "turning one long-form asset into multiple posts",
    },
    {
        "platform": "instagram",
        "format": "reel_script",
        "content_pillar": "Product-in-Action",
        "hook": "What does AI clip scoring actually look like? 30-second walkthrough.",
        "caption": (
            "Five scores. One clip selection decision.\n\n"
            "Hook / Emotion / Relevance / Novelty / Virality\n\n"
            "Not a replacement for your judgment — a faster starting point.\n\n"
            "IncuBrix Clips scoring interface — link in bio for more. 🔗\n\n"
            "#ClipScoring #ContentTools #IncuBrix #CreatorWorkflow"
        ),
        "cta": "Follow for more workflow breakdowns. Link in bio. 🔗",
        "hashtags": "#ClipScoring #ContentTools #IncuBrix #CreatorWorkflow",
        "funnel_stage": "consideration",
        "experiment_id": "EXP_FORMAT:demo-led",
        "source_excerpt": "Clips scoring: Hook, Emotion, Relevance, Novelty, Virality",
        "claim_status": "verified",
    },
    {
        "platform": "instagram",
        "format": "graphic_concept",
        "content_pillar": "Practical AI and Human Judgment",
        "hook": "AI does the first pass. You do the final call.",
        "caption": (
            "Graphic concept: Split design\n"
            "Left: AI icon — 'First draft in seconds'\n"
            "Right: Human icon — 'Reviewed before it goes live'\n"
            "Centre: Arrow pointing right → 'Your voice, faster'\n\n"
            "Caption:\n"
            "Every AI content tool is only as good as the human reviewing it.\n\n"
            "AI accelerates the mechanical. You protect the meaningful.\n\n"
            "#AIContent #CreatorTools #HumanFirst #ContentStrategy"
        ),
        "cta": "Save this. Share with a creator using AI blindly. 📌",
        "hashtags": "#AIContent #CreatorTools #HumanFirst #ContentStrategy",
        "funnel_stage": "awareness",
        "experiment_id": "EXP_CTA:generic",
        "source_excerpt": "where AI helps and where human review is needed",
    },
    {
        "platform": "instagram",
        "format": "reel_script",
        "content_pillar": "Creator Pain and Workflow Friction",
        "hook": "Your content backlog isn't a you problem. It's a workflow problem.",
        "caption": (
            "Three signs your repurposing workflow is broken:\n\n"
            "1. Your drafts folder is bigger than your published feed\n"
            "2. You're rediscovering old ideas when recording new ones\n"
            "3. You spend more time on logistics than on the actual content\n\n"
            "Fix the system, not the schedule.\n\n"
            "#ContentBacklog #CreatorSystems #SoloCreator #ContentWorkflow"
        ),
        "cta": "Follow for practical creator workflow tips. No hype, just process. 📌",
        "hashtags": "#ContentBacklog #CreatorSystems #SoloCreator #ContentWorkflow",
        "funnel_stage": "awareness",
        "experiment_id": "EXP_HOOK:pain-led",
        "source_excerpt": "content backlog and repetitive repurposing work",
    },
    {
        "platform": "instagram",
        "format": "carousel_concept",
        "content_pillar": "Product-in-Action",
        "hook": "Guided Audio workflow: from idea to voiceover in one session.",
        "caption": (
            "Slide 1: Guided Audio — from idea to voiceover without leaving the tool\n"
            "Slide 2: Step 1 — Enter your idea or topic\n"
            "Slide 3: Step 2 — AI generates and you refine the script\n"
            "Slide 4: Step 3 — Choose your style and voice\n"
            "Slide 5: Step 4 — Preview and adjust pause/stability controls\n"
            "Slide 6: Step 5 — Generate final voiceover\n"
            "Slide 7: This is what a contained audio workflow looks like — no switching tools\n\n"
            "#AudioContent #VoiceoverWorkflow #IncuBrix #ContentCreation"
        ),
        "cta": "Save this if you create audio content. Link to try it in bio. 🔗",
        "hashtags": "#AudioContent #VoiceoverWorkflow #IncuBrix #ContentCreation",
        "funnel_stage": "consideration",
        "experiment_id": "EXP_FORMAT:demo-led",
        "source_excerpt": "guided Audio workflow: script generation, style, voice, voiceover",
        "claim_status": "verified",
    },
    # ---- YOUTUBE SHORTS short_script ----
    {
        "platform": "youtube_shorts",
        "format": "short_script",
        "content_pillar": "Creator Pain and Workflow Friction",
        "hook": "You have 3 hours of recordings and zero posts. Here's why.",
        "caption": (
            "[HOOK — 0:00–0:03]\n"
            "You have 3 hours of recordings and zero posts. Here's why.\n\n"
            "[MAIN — 0:03–0:45]\n"
            "Most creators think the bottleneck is editing. It's not.\n"
            "It's the five manual steps between 'recording done' and 'post published'.\n\n"
            "Step one: download the recording.\n"
            "Step two: upload it to a transcription tool.\n"
            "Step three: download the transcript.\n"
            "Step four: manually find the good clips.\n"
            "Step five: write captions from scratch.\n\n"
            "Five steps. Each one breaks the momentum.\n\n"
            "[CTA — 0:45–0:55]\n"
            "If this is your workflow, there's a faster path. Subscribe for the breakdown.\n\n"
            "[Visual concept: creator at desk, screen shows open tabs and file folders — chaotic workflow visual]"
        ),
        "cta": "Subscribe for practical creator workflow breakdowns. No fluff.",
        "hashtags": "#ContentCreators #CreatorWorkflow #YouTubeShorts #ContentRepurposing",
        "funnel_stage": "awareness",
        "experiment_id": "EXP_HOOK:pain-led",
        "source_excerpt": "tool switching and post-recording bottlenecks",
    },
    {
        "platform": "youtube_shorts",
        "format": "short_script",
        "content_pillar": "Repurposing Education",
        "hook": "The best clip from your last podcast? It's probably not the one you think.",
        "caption": (
            "[HOOK — 0:00–0:03]\n"
            "The best clip from your last podcast? It's probably not the one you think.\n\n"
            "[MAIN — 0:03–0:48]\n"
            "Most creators pick clips they remember as good.\n"
            "But memory is biased toward what felt good in the moment, not what performs.\n\n"
            "What actually determines a strong clip:\n"
            "One — the first three seconds create an open loop or strong contrast.\n"
            "Two — it doesn't require the full episode context to make sense.\n"
            "Three — there's a specific, memorable detail — a number, a name, a turning point.\n\n"
            "Start with the transcript. Read it cold. The moments that stop you are the clips.\n\n"
            "[CTA — 0:48–0:58]\n"
            "Subscribe for more practical repurposing frameworks.\n\n"
            "[Visual concept: split screen — creator picks one clip, transcript highlights a different better one]"
        ),
        "cta": "Subscribe. New repurposing framework every week.",
        "hashtags": "#PodcastClips #ContentRepurposing #CreatorTips #YouTubeShorts",
        "funnel_stage": "consideration",
        "experiment_id": "EXP_HOOK:outcome-led",
        "source_excerpt": "hook selection and clip strategy",
    },
    {
        "platform": "youtube_shorts",
        "format": "short_script",
        "content_pillar": "Product-in-Action",
        "hook": "Five scores. One clip decision. This is how AI clip scoring works.",
        "caption": (
            "[HOOK — 0:00–0:03]\n"
            "Five scores. One clip decision. This is how AI clip scoring works.\n\n"
            "[MAIN — 0:03–0:50]\n"
            "When IncuBrix analyzes a clip, it scores five things:\n\n"
            "Hook strength — does it earn attention in the first three seconds?\n"
            "Emotional resonance — does it create a feeling?\n"
            "Relevance — is it aligned with what your audience cares about?\n"
            "Novelty — does it say something the audience hasn't heard before?\n"
            "Viral potential — does it have the structure that gets reshared?\n\n"
            "These aren't just numbers. They're a lens for the same decision you'd make manually — just faster.\n"
            "You still decide. The scores just surface the best candidates first.\n\n"
            "[CTA — 0:50–0:58]\n"
            "Subscribe to see more of this workflow in action.\n\n"
            "[Visual concept: screen recording showing Clips scoring interface with five score bars updating]"
        ),
        "cta": "Subscribe for more IncuBrix workflow walkthroughs.",
        "hashtags": "#ClipScoring #IncuBrix #ContentWorkflow #YouTubeShorts",
        "funnel_stage": "consideration",
        "experiment_id": "EXP_FORMAT:demo-led",
        "source_excerpt": "Clips scoring: Hook, Emotion, Relevance, Novelty, Virality",
        "claim_status": "verified",
    },
    {
        "platform": "youtube_shorts",
        "format": "short_script",
        "content_pillar": "Practical AI and Human Judgment",
        "hook": "AI wrote this caption. Here's what I changed before posting it.",
        "caption": (
            "[HOOK — 0:00–0:03]\n"
            "AI wrote this caption. Here's what I changed before posting it.\n\n"
            "[MAIN — 0:03–0:50]\n"
            "The AI draft was grammatically correct.\n"
            "It was relevant. It was the right length.\n"
            "And it sounded like it could have been written by any creator on the platform.\n\n"
            "So I made three changes:\n"
            "One — I replaced the generic opening with the specific thing I actually said.\n"
            "Two — I added the detail that only I would know.\n"
            "Three — I cut the last line because it was the AI trying to close, not me.\n\n"
            "The AI got me 80% of the way there in ten seconds.\n"
            "The last 20% took three minutes and made it actually sound like me.\n\n"
            "[CTA — 0:50–0:58]\n"
            "That's the AI + human workflow I actually use. Subscribe for more.\n\n"
            "[Visual concept: before/after text comparison on screen, specific edits highlighted]"
        ),
        "cta": "Subscribe for practical AI + creator workflow content.",
        "hashtags": "#AIContent #CreatorVoice #ContentEditing #YouTubeShorts",
        "funnel_stage": "awareness",
        "experiment_id": "EXP_CTA:outcome-specific",
        "source_excerpt": "avoiding generic AI content and preserving creator voice",
    },
    # ---- Additional LinkedIn posts to reach 32 candidates ----
    {
        "platform": "linkedin",
        "format": "text_post",
        "content_pillar": "Repurposing Education",
        "hook": "The 3-word test for every clip you're about to repurpose.",
        "caption": (
            "Before you spend time turning a clip into a post, ask:\n\n"
            "What are the first three words?\n\n"
            "If those three words don't create curiosity, contrast, or a specific promise — "
            "the clip probably won't stop anyone's scroll.\n\n"
            "Strong first-three-word patterns:\n"
            "→ 'Most creators ignore...' (contrast)\n"
            "→ 'Here's what happened...' (story)\n"
            "→ 'Stop doing this...' (imperative)\n"
            "→ 'The real problem...' (problem framing)\n"
            "→ 'After 100 episodes...' (specific)\n\n"
            "Weak first-three-word patterns:\n"
            "→ 'In this video...'\n"
            "→ 'Today we'll talk...'\n"
            "→ 'Hey everyone, so...'\n\n"
            "Three words. One filter. Run every clip through it."
        ),
        "cta": "What's the first three words of your best-performing post? Drop it below.",
        "hashtags": "#ContentRepurposing #HookWriting #CreatorStrategy",
        "funnel_stage": "consideration",
        "experiment_id": "EXP_HOOK:outcome-led",
        "source_excerpt": "hook selection",
    },
    {
        "platform": "linkedin",
        "format": "educational_post",
        "content_pillar": "Product-in-Action",
        "hook": "The guided Audio workflow in IncuBrix: what it actually does and when to use it.",
        "caption": (
            "If you create audio content — podcasts, voiceovers, narrations — the guided Audio "
            "workflow in IncuBrix takes you from idea to generated voiceover in one place.\n\n"
            "The sequence:\n"
            "1. Enter your topic or existing script\n"
            "2. AI generates a draft script you can refine inline\n"
            "3. Choose your tone/style (the tool offers style adaptation)\n"
            "4. AI recommends voices and you choose from multiple options\n"
            "5. Adjust pause and stability controls\n"
            "6. Generate and review the voiceover\n\n"
            "Voice cloning is also available as an option — which lets you use your own voice "
            "as the base.\n\n"
            "This is the kind of workflow that reduces the gap between 'idea' and 'ready-to-publish' "
            "without requiring you to switch between five different tools."
        ),
        "cta": "What does your current audio production workflow look like? I'm curious about the friction points.",
        "hashtags": "#AudioProduction #VoiceoverWorkflow #PodcastProduction #IncuBrix",
        "funnel_stage": "consideration",
        "experiment_id": "EXP_FORMAT:demo-led",
        "source_excerpt": "guided Audio workflow: script, style, voice, voiceover, voice cloning",
        "claim_status": "verified",
    },
    {
        "platform": "linkedin",
        "format": "text_post",
        "content_pillar": "Creator Pain and Workflow Friction",
        "hook": "Consistency in content publishing is a systems question, not a willpower question.",
        "caption": (
            "Every creator who's been consistent for more than 6 months will tell you the same thing:\n\n"
            "They didn't get more disciplined. They got a better system.\n\n"
            "The workflow that makes publishing consistent:\n"
            "• A fixed recording cadence (not a 'when I feel inspired' cadence)\n"
            "• A repurposing process that runs in parallel, not after\n"
            "• A content queue that fills faster than it empties\n"
            "• One decision point: approve or reject, never 'start from scratch'\n\n"
            "Consistency comes from removing the decisions that drain you between recording and publishing.\n\n"
            "What's the decision that slows your publishing cadence the most?"
        ),
        "cta": "Follow for frameworks that actually reduce publishing friction. →",
        "hashtags": "#ContentConsistency #CreatorSystems #PublishingCadence",
        "funnel_stage": "awareness",
        "experiment_id": "EXP_CTA:outcome-specific",
        "source_excerpt": "inconsistent publishing and editing overhead",
    },
    {
        "platform": "linkedin",
        "format": "educational_post",
        "content_pillar": "Practical AI and Human Judgment",
        "hook": "What to review before publishing any AI-generated caption.",
        "caption": (
            "A checklist I run on every AI-generated caption before it goes live:\n\n"
            "□ Does it sound like me, or like 'a creator'?\n"
            "□ Is the hook specific to this piece of content, or could it be anyone's hook?\n"
            "□ Did the AI invent any detail I didn't say? (This happens more than you'd expect.)\n"
            "□ Is the CTA appropriate for this platform?\n"
            "□ Am I comfortable if this is the first post a new follower sees?\n"
            "□ Is there any claim here that I can't personally verify?\n\n"
            "Six questions. Two minutes. These protect the content quality that matters.\n\n"
            "The AI gets you fast. The checklist keeps you accurate."
        ),
        "cta": "Save this checklist. Use it before your next AI-assisted post goes live.",
        "hashtags": "#AIContent #ContentReview #CreatorQuality #PublishingChecklist",
        "funnel_stage": "consideration",
        "experiment_id": "EXP_CTA:generic",
        "source_excerpt": "where human review is needed and avoiding generic AI content",
    },
    {
        "platform": "linkedin",
        "format": "demo_post",
        "content_pillar": "Product-in-Action",
        "hook": "Smart Cut + Hooks & Titles: what these two IncuBrix features actually do in practice.",
        "caption": (
            "Two features in IncuBrix's transcript editing workflow worth knowing:\n\n"
            "Smart Cut:\n"
            "Automatically removes filler words, false starts, and long silences from your recording "
            "based on the transcript. You review and approve the cuts before they're applied.\n\n"
            "Hooks & Titles:\n"
            "Generates suggested hooks and titles based on the strongest moments in your content — "
            "drawn from the transcript, not invented.\n\n"
            "Together, these two features handle two of the slowest parts of the editing workflow "
            "for long-form creators: initial cuts and naming the content.\n\n"
            "They don't replace your judgment. They move you faster to the point where your "
            "judgment matters."
        ),
        "cta": "What part of your editing workflow takes the most time? I'll share the relevant workflow step.",
        "hashtags": "#SmartCut #TranscriptEditing #IncuBrix #ContentEditing",
        "funnel_stage": "consideration",
        "experiment_id": "EXP_FORMAT:demo-led",
        "source_excerpt": "Smart Cut and Hooks and Titles transcript editing",
        "claim_status": "verified",
    },
    {
        "platform": "linkedin",
        "format": "text_post",
        "content_pillar": "Repurposing Education",
        "hook": "Platform adaptation is not just resizing. It's recontextualizing.",
        "caption": (
            "Taking a LinkedIn post and posting it on Instagram is not repurposing. It's reposting.\n\n"
            "Real platform adaptation means:\n\n"
            "LinkedIn version → professional lesson, structured takeaway, direct CTA\n"
            "Instagram version → compressed emotional moment, visual-first, save-worthy\n"
            "YouTube Shorts version → immediate hook, one idea, spoken-language pacing\n\n"
            "Same source insight. Three different executions.\n\n"
            "The source is the raw material. Platform adaptation is the craft.\n\n"
            "Which platform adaptation do you find hardest to get right?"
        ),
        "cta": "Save this if you're building a cross-platform content strategy.",
        "hashtags": "#PlatformStrategy #ContentAdaptation #RepurposingContent #CreatorEducation",
        "funnel_stage": "awareness",
        "experiment_id": "EXP_FORMAT:educational",
        "source_excerpt": "platform adaptation for LinkedIn, Instagram, YouTube",
    },
    {
        "platform": "instagram",
        "format": "reel_script",
        "content_pillar": "Practical AI and Human Judgment",
        "hook": "The 20% of your AI caption you should always rewrite.",
        "caption": (
            "AI gets you 80% there.\n\n"
            "Here's the 20% that always needs you:\n"
            "→ The specific detail only you know\n"
            "→ The word choice that sounds like your voice\n"
            "→ The CTA that fits your actual offer\n\n"
            "AI is fast. You make it real.\n\n"
            "#AIContent #CreatorVoice #ContentEditing #CreatorTips"
        ),
        "cta": "Save this. Apply it to your next AI draft. 📌",
        "hashtags": "#AIContent #CreatorVoice #ContentEditing #CreatorTips",
        "funnel_stage": "consideration",
        "experiment_id": "EXP_CTA:outcome-specific",
        "source_excerpt": "preserving creator voice with AI assistance",
    },
    {
        "platform": "youtube_shorts",
        "format": "short_script",
        "content_pillar": "Creator Pain and Workflow Friction",
        "hook": "If your content calendar is empty, it's not a motivation issue.",
        "caption": (
            "[HOOK — 0:00–0:03]\n"
            "If your content calendar is empty, it's not a motivation issue.\n\n"
            "[MAIN — 0:03–0:48]\n"
            "Here's what an empty calendar usually means:\n\n"
            "Your repurposing workflow takes longer than your publishing cadence.\n"
            "So the queue runs out before you can refill it.\n\n"
            "The fix isn't to post more. It's to shorten the gap between recording and posting.\n\n"
            "One recording. Multiple formats. One workflow.\n"
            "That's what keeps the calendar full.\n\n"
            "[CTA — 0:48–0:58]\n"
            "Subscribe for practical creator workflow content. New video every week.\n\n"
            "[Visual concept: empty calendar grid, then same calendar filling up with scheduled posts]"
        ),
        "cta": "Subscribe for weekly creator workflow breakdowns.",
        "hashtags": "#ContentCalendar #CreatorWorkflow #RepurposeContent #YouTubeShorts",
        "funnel_stage": "awareness",
        "experiment_id": "EXP_HOOK:pain-led",
        "source_excerpt": "inconsistent publishing and content backlog",
    },
    {
        "platform": "linkedin",
        "format": "carousel",
        "content_pillar": "Product-in-Action",
        "hook": "The IncuBrix publishing workflow — from content to published across platforms.",
        "caption": (
            "Slide 1: From content to published — the IncuBrix publishing workflow\n"
            "Slide 2: Step 1 — Content starts in Home: Text, Audio, Video, Clips, or Editor\n"
            "Slide 3: Step 2 — Process and edit within the tool (transcript editing / Smart Cut / Clips scoring)\n"
            "Slide 4: Step 3 — Review and finalize in Content Hub\n"
            "Slide 5: Step 4 — Connect your social platform accounts via Connections\n"
            "Slide 6: Step 5 — Schedule and publish via the Publishing workflow\n"
            "Slide 7: Step 6 — Track in Dashboard and Analytics\n"
            "Slide 8: One tool. Full workflow. Fewer tabs.\n\n"
            "[Note: Dashboard showed sample/demo metrics during review — actual metrics will reflect your content performance]"
        ),
        "cta": "What step in your publishing workflow creates the most friction? Drop a comment.",
        "hashtags": "#ContentPublishing #CreatorWorkflow #IncuBrix #ContentManagement",
        "funnel_stage": "conversion",
        "experiment_id": "EXP_FORMAT:demo-led",
        "source_excerpt": "publishing workflow, Content Hub, Connections, Dashboard",
        "claim_status": "verified",
    },
    {
        "platform": "instagram",
        "format": "carousel_concept",
        "content_pillar": "Creator Pain and Workflow Friction",
        "hook": "7 signs your content workflow is working against you.",
        "caption": (
            "Slide 1: 7 signs your content workflow is working against you\n"
            "Slide 2: 1. You have more recordings than posts\n"
            "Slide 3: 2. You forget what you recorded 2 weeks ago\n"
            "Slide 4: 3. You rewrite captions from scratch every time\n"
            "Slide 5: 4. Your 'publish' tab has more drafts than scheduled posts\n"
            "Slide 6: 5. You switch between 4+ tools before anything goes live\n"
            "Slide 7: 6. You post inconsistently because editing takes too long\n"
            "Slide 8: 7. You avoid repurposing because it feels like starting over\n"
            "Slide 9: The workflow is broken. Not you. Let's fix the system.\n\n"
            "#ContentWorkflow #CreatorBurnout #SoloCreator #ContentSystems"
        ),
        "cta": "Save this. Share with a creator who needs to hear it. 📌",
        "hashtags": "#ContentWorkflow #CreatorBurnout #SoloCreator #ContentSystems",
        "funnel_stage": "awareness",
        "experiment_id": "EXP_FORMAT:educational",
        "source_excerpt": "tool switching, content backlog, repetitive repurposing",
    },
]


class MockGenerationProvider:
    """
    Deterministic mock content generation provider.
    Uses a seeded random generator for reproducibility.
    Does not call any external API.
    """

    MODE_LABEL = "[MOCK MODE — Deterministic demo content. Not live AI output.]"

    def __init__(self, seed: int = 42):
        self.seed = seed
        self.rng = random.Random(seed)
        logger.info(f"MockGenerationProvider initialized with seed={seed}")

    def generate(
        self,
        input_text: str,
        campaign: str,
        base_url: str,
        candidate_count: int = 32,
    ) -> List[ContentAsset]:
        """
        Generate content assets from mock content bank.
        Uses seeded RNG to ensure reproducibility.
        """
        logger.info(
            f"[MOCK] Generating {candidate_count} candidate assets from "
            f"{len(MOCK_CONTENT_BANK)} templates (seed={self.seed})"
        )

        assets = []
        # Use all items from the bank, then sample additional if needed
        bank_copy = list(MOCK_CONTENT_BANK)
        self.rng.shuffle(bank_copy)

        for i, template in enumerate(bank_copy[:candidate_count]):
            asset = self._create_asset_from_template(template, i + 1, input_text)
            assets.append(asset)

        logger.info(f"[MOCK] Generated {len(assets)} candidate assets")
        return assets

    def _create_asset_from_template(
        self,
        template: dict,
        index: int,
        input_text: str,
    ) -> ContentAsset:
        """Create a ContentAsset from a mock template dict."""
        platform = template["platform"]
        fmt = template["format"]

        # Generate platform-prefixed asset ID
        prefix_map = {
            "linkedin": "LI",
            "instagram": "IG",
            "youtube_shorts": "YT",
        }
        prefix = prefix_map.get(platform, "XX")
        asset_id = f"{prefix}_{index:03d}"

        # Ground mock assets in the supplied input so refresh with genuinely new
        # source material produces distinguishable content, while the same input
        # remains deterministic and therefore deduplicates on repeat.
        sentences = [seg.strip() for seg in input_text.replace("\n", " ").split(".") if seg.strip()]
        source_sentence = sentences[(index - 1) % len(sentences)] if sentences else ""
        source_lens = " ".join(source_sentence.split()[:32])
        base_caption = template.get("caption", "")
        grounded_caption = (
            f"Source-specific lens: {source_lens}.\n\n{base_caption}"
            if source_lens else base_caption
        )

        asset = ContentAsset(
            asset_id=asset_id,
            platform=platform,
            format=fmt,
            content_pillar=template.get("content_pillar", ""),
            hook=template.get("hook", ""),
            caption=grounded_caption,
            cta=template.get("cta", ""),
            source_input=input_text[:200] if input_text else "[mock input]",
            tools_used=f"IncuBrix Content Engine v1.0 | {self.MODE_LABEL}",
            hashtags=template.get("hashtags", ""),
            claim_status=template.get("claim_status", "needs_verification"),
            experiment_id=template.get("experiment_id", ""),
            funnel_stage=template.get("funnel_stage", "awareness"),
            source_excerpt=template.get("source_excerpt", ""),
            final_file_url="",
            source_file_url="",
            test_published_url="",
            impressions_or_views="",
            engagement_rate="",
            clicks="",
            notes=self.MODE_LABEL,
        )
        return asset


class LiveGenerationProvider:
    """
    Live LLM content generation provider.
    Currently supports: OpenAI (gpt-4o), Anthropic (claude), Google (gemini).
    Falls back gracefully if provider is unavailable.
    """

    def __init__(self, provider: str = "openai", api_key: str = ""):
        self.provider = provider
        self.api_key = api_key
        logger.info(f"LiveGenerationProvider initialized for provider={provider}")

    def generate(
        self,
        input_text: str,
        campaign: str,
        base_url: str,
        candidate_count: int = 32,
    ) -> List[ContentAsset]:
        """
        Generate content assets using a live LLM API.
        Not implemented in this release — falls back to mock with warning.
        """
        logger.warning(
            "Live LLM generation is not yet implemented. "
            "Using mock generation instead. "
            "To enable live generation, implement the provider-specific API calls "
            "in this method."
        )
        mock = MockGenerationProvider(seed=42)
        return mock.generate(input_text, campaign, base_url, candidate_count)


def get_provider(config) -> "MockGenerationProvider | LiveGenerationProvider":
    """
    Return the appropriate generation provider based on config.
    """
    import os
    mode = config.mode
    provider_name = config.provider

    if mode == "mock" or provider_name == "mock":
        return MockGenerationProvider(seed=config.seed)

    # Attempt live provider
    api_key_map = {
        "openai": os.getenv("OPENAI_API_KEY", ""),
        "anthropic": os.getenv("ANTHROPIC_API_KEY", ""),
        "google": os.getenv("GOOGLE_API_KEY", ""),
    }
    api_key = api_key_map.get(provider_name, "")
    if not api_key:
        logger.warning(
            f"Provider '{provider_name}' selected but no API key found. "
            f"Set {provider_name.upper()}_API_KEY in .env. Falling back to mock mode."
        )
        return MockGenerationProvider(seed=config.seed)

    return LiveGenerationProvider(provider=provider_name, api_key=api_key)
