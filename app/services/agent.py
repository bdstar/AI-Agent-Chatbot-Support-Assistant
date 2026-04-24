import operator
from typing import Annotated, TypedDict
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from app.config import settings
from app.services.retriever import retrieve_context


# ─────────────────────────────────────────────
# 1. State Definition
# ─────────────────────────────────────────────

class AgentState(TypedDict):
    """State that flows through the LangGraph agent."""
    messages: Annotated[list[BaseMessage], operator.add]
    user_query: str
    context: str
    references: list[dict]
    response: str


# ─────────────────────────────────────────────
# 2. System Prompt
# ─────────────────────────────────────────────

SYSTEM_PROMPT = """You are an expert Life Insurance Support Assistant. Your role is to provide accurate, helpful, and clear answers about life insurance topics.

INSTRUCTIONS:
1. Answer questions based ONLY on the provided context from our knowledge base.
2. If the context contains relevant information, provide a comprehensive answer citing the sources.
3. If the context does NOT contain enough information to answer the question, clearly state: "I don't have enough information in our knowledge base to answer this question accurately. Please consult with a licensed insurance professional."
4. Be professional, empathetic, and clear in your responses.
5. When explaining insurance concepts, use simple language that anyone can understand.
6. If the user asks about specific policy details, remind them to check their actual policy documents.
7. Structure your answers with clear paragraphs for readability.
8. Do not make up information or speculate beyond what the documents provide.

CONTEXT FROM KNOWLEDGE BASE:
{context}

If no context is provided or the context is empty, you can still answer general life insurance questions using your knowledge, but clearly indicate that the answer is based on general knowledge rather than specific documents."""


# ─────────────────────────────────────────────
# 3. Node Functions
# ─────────────────────────────────────────────

def retrieve_node(state: AgentState) -> dict:
    """
    Retrieve relevant documents from ChromaDB based on the user query.
    """
    query = state["user_query"]
    references = retrieve_context(query)

    # Build context string from retrieved documents
    if references:
        context_parts = []
        for i, ref in enumerate(references, 1):
            source_info = f"[Source: {ref['source']}"
            if ref.get("page"):
                source_info += f", Page {ref['page']}"
            source_info += "]"
            context_parts.append(f"--- Document {i} {source_info} ---\n{ref['content']}")
        context = "\n\n".join(context_parts)
    else:
        context = "No relevant documents found in the knowledge base."

    return {
        "context": context,
        "references": references,
    }


def generate_node(state: AgentState) -> dict:
    """
    Generate a response using the LLM with the retrieved context.
    """
    llm = ChatOpenAI(
        model=settings.LLM_MODEL,
        openai_api_key=settings.OPENAI_API_KEY,
        temperature=0.3,
    )

    # Build the system message with context
    system_msg = SystemMessage(content=SYSTEM_PROMPT.format(context=state["context"]))

    # Get conversation history (excluding the current system message handling)
    conversation_messages = [system_msg] + state["messages"]

    # Generate response
    response = llm.invoke(conversation_messages)

    return {
        "response": response.content,
        "messages": [AIMessage(content=response.content)],
    }


# ─────────────────────────────────────────────
# 4. Build the LangGraph Workflow
# ─────────────────────────────────────────────

def build_agent_graph() -> StateGraph:
    """
    Build and compile the LangGraph agent workflow.

    Flow: START → retrieve → generate → END
    """
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("generate", generate_node)

    # Define edges
    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve", "generate")
    workflow.add_edge("generate", END)

    # Compile the graph
    return workflow.compile()


# ─────────────────────────────────────────────
# 5. Agent Interface
# ─────────────────────────────────────────────

# Compile the agent graph once
agent = build_agent_graph()


def process_query(user_message: str, chat_history: list[dict] = None) -> dict:
    """
    Process a user query through the LangGraph agent.

    Args:
        user_message: The user's question
        chat_history: Previous conversation messages [{"role": "user"/"ai", "content": "..."}]

    Returns:
        Dict with keys: response, references
    """
    # Build message history
    messages = []
    if chat_history:
        for msg in chat_history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "ai":
                messages.append(AIMessage(content=msg["content"]))

    # Add current user message
    messages.append(HumanMessage(content=user_message))

    # Invoke the agent
    result = agent.invoke({
        "messages": messages,
        "user_query": user_message,
        "context": "",
        "references": [],
        "response": "",
    })

    # Format references for the response
    formatted_refs = []
    for ref in result.get("references", []):
        formatted_refs.append({
            "source": ref.get("source", "Unknown"),
            "content": ref.get("content", ""),
            "page": ref.get("page"),
        })

    return {
        "response": result.get("response", "I'm sorry, I couldn't generate a response. Please try again."),
        "references": formatted_refs,
    }
