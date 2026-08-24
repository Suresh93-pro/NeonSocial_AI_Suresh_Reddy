import os

from typing import TypedDict

from dotenv import load_dotenv

from langgraph.graph import StateGraph, END


load_dotenv()


# ============================================================
# SOCIAL MEDIA STATE
# ============================================================

class SocialState(TypedDict, total=False):

    topic: str

    platform: str

    tone: str

    content: str

    status: str

    feedback: str


# ============================================================
# AI CONFIGURATION
# ============================================================

def get_ai_model():

    api_key = os.getenv(
        "OPENAI_API_KEY"
    )

    if not api_key:

        return None

    try:

        from langchain_openai import ChatOpenAI

        return ChatOpenAI(

            model="gpt-4.1-mini",

            api_key=api_key,

            temperature=0.8

        )

    except Exception as error:

        print(
            "[AI MODEL ERROR]",
            error
        )

        return None


# ============================================================
# GENERATE SOCIAL MEDIA CONTENT
# ============================================================

def generate_content(state: SocialState):

    topic = state.get(
        "topic",
        "AI technology"
    )

    platform = state.get(
        "platform",
        "LinkedIn"
    )

    tone = state.get(
        "tone",
        "Professional"
    )


    api_key = os.getenv(
        "OPENAI_API_KEY"
    )


    demo_mode = os.getenv(
        "DEMO_MODE",
        "true"
    ).lower() == "true"


    # ========================================================
    # DEMO MODE
    # ========================================================

    if demo_mode or not api_key:

        content = f"""🚀 {topic}

AI is transforming the way we learn,
work and create.

The biggest opportunity is not simply
replacing people with technology.

It is giving people better tools to become
more productive, creative and innovative.

The future belongs to people who continuously
learn, adapt and experiment.

What do you think about the future of {topic.lower()}?

#AI #Technology #Innovation #Future
"""


    # ========================================================
    # REAL AI MODE
    # ========================================================

    else:

        model = get_ai_model()


        if model is None:

            raise Exception(
                "AI model could not be initialized."
            )


        prompt = f"""
You are an expert social media content strategist.

Create a high-quality {platform} post.

Topic:
{topic}

Tone:
{tone}

Requirements:

- Strong opening hook
- Useful original content
- Natural human writing
- Easy to read
- No unnecessary headings
- Appropriate emojis
- Strong closing question or CTA
- Relevant hashtags
- Do not mention that you are an AI
- Do not fabricate statistics
- Platform-appropriate length

Return ONLY the final social media post.
"""


        result = model.invoke(
            prompt
        )


        content = result.content


    return {

        **state,

        "content":
            content,

        "status":
            "WAITING_FOR_APPROVAL"

    }


# ============================================================
# HUMAN APPROVAL
# ============================================================

def human_approval(state: SocialState):

    return {

        **state,

        "status":
            "WAITING_FOR_APPROVAL"

    }


# ============================================================
# LANGGRAPH
# ============================================================

def build_graph():

    graph = StateGraph(
        SocialState
    )


    graph.add_node(
        "generate",
        generate_content
    )


    graph.add_node(
        "approval",
        human_approval
    )


    graph.set_entry_point(
        "generate"
    )


    graph.add_edge(
        "generate",
        "approval"
    )


    graph.add_edge(
        "approval",
        END
    )


    return graph.compile()


social_graph = build_graph()


# ============================================================
# CREATE SOCIAL MEDIA POST
# ============================================================

def create_post(
    topic: str,
    platform: str,
    tone: str
):

    initial_state = {

        "topic":
            topic,

        "platform":
            platform,

        "tone":
            tone,

        "status":
            "GENERATING"

    }


    result = social_graph.invoke(
        initial_state
    )


    return result


# ============================================================
# NEON AI ASSISTANT
# ============================================================

def chat_with_ai(message: str):

    message = str(
        message or ""
    ).strip()


    if not message:

        return (
            "Please enter a message."
        )


    api_key = os.getenv(
        "OPENAI_API_KEY"
    )


    demo_mode = os.getenv(
        "DEMO_MODE",
        "true"
    ).lower() == "true"


    # ========================================================
    # DEMO AI ASSISTANT
    # ========================================================

    if demo_mode or not api_key:

        lower_message = message.lower()


        # ----------------------------------------------------
        # AI POST IDEAS
        # ----------------------------------------------------

        if (
            "5" in lower_message
            and
            "linkedin" in lower_message
            and
            "idea" in lower_message
        ):

            return """Here are 5 LinkedIn post ideas about AI:

1. 🤖 How AI is changing the way students learn

Share practical examples of how AI tools can help students research, understand difficult concepts and learn faster.

2. 🚀 AI skills every student should learn

Discuss prompting, automation, AI-assisted coding, research and responsible AI usage.

3. 💡 AI will not replace everyone — but people using AI may move faster

Explain why learning to work with AI is becoming an important professional skill.

4. 🎓 The future of AI in education

Talk about personalized learning, intelligent tutoring systems and how teachers can use AI effectively.

5. 🔥 What happens when students start building with AI?

Share examples of projects students can create using AI, APIs, automation and agents.

Tip: End each post with a question to encourage meaningful discussion."""


        # ----------------------------------------------------
        # HOOK
        # ----------------------------------------------------

        if (
            "hook" in lower_message
        ):

            return """Here is a powerful LinkedIn hook:

"AI isn't coming for your career.

It's changing the way your career works.

The real question isn't whether AI will change your industry.

It's whether you'll learn to use it before someone else does."

This works because it creates curiosity, contrast and encourages the reader to continue."""


        # ----------------------------------------------------
        # CONTENT STRATEGY
        # ----------------------------------------------------

        if (
            "strategy" in lower_message
        ):

            return """A simple LinkedIn content strategy:

Monday → Educational post
Tuesday → Personal learning experience
Wednesday → AI/tool tutorial
Thursday → Career or industry insight
Friday → Opinion/question post

Use this structure:

Hook → Problem → Insight → Example → Takeaway → Question

Consistency is more important than posting every day."""


        # ----------------------------------------------------
        # CAPTION
        # ----------------------------------------------------

        if (
            "caption" in lower_message
        ):

            return """Try this caption structure:

🔥 Start with a strong statement.

Explain the problem in 2–3 short paragraphs.

Share one useful insight or lesson.

Finish with a question.

Example:

"AI is changing faster than most people realize.

The advantage isn't simply having access to AI tools.

The advantage comes from knowing how to use them effectively.

What AI tool has helped you the most?" """


        # ----------------------------------------------------
        # DEFAULT DEMO RESPONSE
        # ----------------------------------------------------

        return f"""Great question, Suresh! 👋

You asked:

"{message}"

For NeonSocial AI, I recommend turning this into a social-media workflow:

1. Define the idea
2. Create a strong hook
3. Generate useful content
4. Add a clear CTA
5. Review the content
6. Approve it
7. Schedule it
8. Publish it

Try asking me something like:

• Give me 5 LinkedIn post ideas about AI
• Write a powerful LinkedIn hook
• Give me a content strategy for students
• Improve this LinkedIn post
• Write a professional AI caption"""


    # ========================================================
    # REAL AI ASSISTANT
    # ========================================================

    model = get_ai_model()


    if model is None:

        raise Exception(
            "AI model could not be initialized."
        )


    prompt = f"""
You are Neon AI, the intelligent social media
assistant inside NeonSocial AI.

The user is asking:

{message}

Help the user with:

- LinkedIn content
- Social media strategy
- Post ideas
- Hooks
- Captions
- CTAs
- Content improvement
- AI and technology topics
- Student creator strategies

Be concise, useful and practical.

Use bullet points when appropriate.

Do not mention system instructions.

Do not say that you are unavailable.

Answer the user's request directly.
"""


    result = model.invoke(
        prompt
    )


    return result.content