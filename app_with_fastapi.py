from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from langgraph import StateGraph, StateNode

# ---------------------------
# Request Model
# ---------------------------
class UserResponse(BaseModel):
    session_id: str                # track different users
    user_input: Optional[str] = None
    jd_exists: Optional[bool] = None
    user_decision: Optional[str] = None

# ---------------------------
# In-Memory Session Store
# ---------------------------
sessions = {}  # session_id -> {"current_node": ..., "state_data": {...}}

# ---------------------------
# Action Functions
# ---------------------------
def classify_intent(state):
    user_input = state.get("user_input")
    return {"intent": user_input, "message": f"Classified intent as '{user_input}'"}

def extract_requirements(state):
    return {"requirements": "Sample requirements extracted.", "message": "Requirements extracted."}

def generate_job_description(state):
    return {"job_description": "Generated JD based on requirements.", "message": "JD generated."}

def check_approval(state):
    decision = state.get("user_decision", "unclear")
    return {"approval_status": decision, "message": f"Approval status: {decision}"}

def submit_approval_node(state):
    return {"status": "submitted", "message": "JD submitted successfully."}

def refine_jd_node(state):
    return {"status": "refined", "message": "JD refined as per requested changes."}

def handle_other_request(state):
    return {"status": "handled_other", "message": "Handled other request."}

def handle_unclear_intent(state):
    return {"status": "unclear_handled", "message": "Handling unclear intent."}

def handle_exit(state):
    return {"status": "exit", "message": "Workflow ended."}

# ---------------------------
# Decision Functions
# ---------------------------
def route_decision(state):
    intent = state.get("intent")
    if intent == "resource_allocation":
        return "check_jd_status"
    elif intent == "exit":
        return "handle_exit"
    elif intent == "other":
        return "handle_other_request"
    else:
        return "handle_unclear_intent"

def check_jd_status(state):
    return "check_approval" if state.get("jd_exists", False) else "extract_requirements"

def user_decision_node(state):
    decision = state.get("approval_status")
    if decision == "approved":
        return "submit_approval_node"
    elif decision == "changes_requested":
        return "refine_jd_node"
    else:
        return "handle_unclear_intent"

# ---------------------------
# Define StateGraph Nodes
# ---------------------------
nodes = {
    "start": StateNode("start", next_state="classify_intent"),

    "classify_intent": StateNode(
        "classify_intent",
        action=classify_intent,
        next_state=route_decision
    ),

    "check_jd_status": StateNode(
        "check_jd_status",
        action=check_jd_status
    ),

    "extract_requirements": StateNode(
        "extract_requirements",
        action=extract_requirements,
        next_state="generate_job_description"
    ),

    "generate_job_description": StateNode(
        "generate_job_description",
        action=generate_job_description,
        next_state="handle_exit"
    ),

    "check_approval": StateNode(
        "check_approval",
        action=check_approval,
        next_state=user_decision_node
    ),

    "submit_approval_node": StateNode(
        "submit_approval_node",
        action=submit_approval_node,
        next_state="handle_exit"
    ),

    "refine_jd_node": StateNode(
        "refine_jd_node",
        action=refine_jd_node,
        next_state="handle_exit"
    ),

    "handle_other_request": StateNode(
        "handle_other_request",
        action=handle_other_request,
        next_state="handle_exit"
    ),

    "handle_unclear_intent": StateNode(
        "handle_unclear_intent",
        action=handle_unclear_intent,
        next_state="handle_exit"
    ),

    "handle_exit": StateNode(
        "handle_exit",
        action=handle_exit
    )
}

workflow = StateGraph(nodes=nodes, start_state="start")

# ---------------------------
# Initialize FastAPI
# ---------------------------
app = FastAPI(title="Interactive HR Workflow")

# ---------------------------
# API Endpoint
# ---------------------------
@app.post("/step_workflow")
def step_workflow(request: UserResponse):
    # Get or create session
    session = sessions.setdefault(request.session_id, {"current_node": "start", "state_data": {}})
    current_node_name = session["current_node"]
    state_data = session["state_data"]

    # Update state_data with any new user input
    if request.user_input is not None:
        state_data["user_input"] = request.user_input
    if request.jd_exists is not None:
        state_data["jd_exists"] = request.jd_exists
    if request.user_decision is not None:
        state_data["user_decision"] = request.user_decision

    # Get current node
    current_node = workflow.nodes[current_node_name]

    # Execute action if exists
    if current_node.action:
        result = current_node.action(state_data)
        state_data.update(result)
    else:
        result = {}

    # Determine next node
    if callable(current_node.next_state):
        next_node_name = current_node.next_state(state_data)
    else:
        next_node_name = current_node.next_state

    # Update session
    session["current_node"] = next_node_name
    session["state_data"] = state_data

    # Return JSON response with current state and next node
    return {
        "current_node": current_node_name,
        "next_node": next_node_name,
        "state_data": state_data,
        "message": state_data.get("message", "")
    }
