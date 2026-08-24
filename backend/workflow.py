from typing import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command


class SocialState(TypedDict, total=False):
    topic: str
    platform: str
    tone: str
    content: str
    status: str
    feedback: str


def generate(state: SocialState):

    topic = state["topic"]

    content = f"""🚀 {topic}

AI is transforming the way people learn, work and create.

The biggest opportunity is not replacing people.

It is helping people become more productive,
creative and innovative.

The future belongs to those who learn continuously.

What do you think?

#AI #Technology #Innovation #Future"""

    return {
        "content": content,
        "status": "WAITING_FOR_APPROVAL",
    }


def human_review(state: SocialState):

    decision = interrupt({
        "type": "SOCIAL_POST_APPROVAL",
        "message": "Review this post before publishing.",
        "content": state["content"],
        "platform": state["platform"],
    })

    if decision == "approve":
        return {
            "status": "APPROVED"
        }

    if decision == "reject":
        return {
            "status": "REJECTED"
        }

    return {
        "status": "REJECTED",
        "feedback": str(decision)
    }


def route_after_review(state: SocialState):

    if state["status"] == "APPROVED":
        return "publish"

    return "finish"


def publish(state: SocialState):

    return {
        "status": "READY_TO_SCHEDULE"
    }


def finish(state: SocialState):

    return state


checkpointer = MemorySaver()

workflow = StateGraph(SocialState)

workflow.add_node("generate", generate)
workflow.add_node("human_review", human_review)
workflow.add_node("publish", publish)
workflow.add_node("finish", finish)

workflow.add_edge(START, "generate")
workflow.add_edge("generate", "human_review")

workflow.add_conditional_edges(
    "human_review",
    route_after_review,
    {
        "publish": "publish",
        "finish": "finish",
    }
)

workflow.add_edge("publish", END)
workflow.add_edge("finish", END)

social_workflow = workflow.compile(
    checkpointer=checkpointer
)