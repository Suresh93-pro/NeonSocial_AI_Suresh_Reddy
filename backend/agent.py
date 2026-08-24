from typing import TypedDict
from langgraph.graph import StateGraph, START, END


class SocialState(TypedDict, total=False):
    topic: str
    platform: str
    tone: str
    content: str
    status: str
    feedback: str


def generate_content(state: SocialState):
    topic = state.get("topic", "")
    platform = state.get("platform", "LinkedIn")
    tone = state.get("tone", "professional")

    content = f"""🚀 {topic}

Technology is changing the way we learn, work and create.

Here are a few thoughts on why this matters:

• Innovation is becoming faster
• AI is helping people work smarter
• New opportunities are being created
• Human creativity remains essential

The future belongs to people who learn, adapt and build.

What do you think?

#AI #Technology #Innovation #Future #Learning"""

    return {
        "content": content,
        "platform": platform,
        "tone": tone,
        "status": "PENDING_REVIEW",
    }


def create_graph():
    workflow = StateGraph(SocialState)

    workflow.add_node("generate", generate_content)

    workflow.add_edge(START, "generate")
    workflow.add_edge("generate", END)

    return workflow.compile()


social_agent = create_graph()


def generate_post(topic, platform="LinkedIn", tone="professional"):
    result = social_agent.invoke({
        "topic": topic,
        "platform": platform,
        "tone": tone,
    })

    return result