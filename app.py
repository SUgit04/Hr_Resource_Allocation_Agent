from langgraph import StateGraph, StateNode

# ---------------------------
# Action Functions (Independent)
# ---------------------------
def classify_intent(state, user_input):
    print(f"[Action] Classifying intent for input: '{user_input}'")
    # For now, just pass input as intent (can call GPT-4 API later)
    return {"intent": user_input}

def extract_requirements(state, **kwargs):
    print("[Action] Extracting requirements for new JD...")
    return {"requirements": "Sample requirements extracted."}

def generate_job_description(state, **kwargs):
    print("[Action] Generating Job Description...")
    return {"job_descSription": "Generated JD based on requirements."}

def check_approval(state, user_decision=None):
    print(f"[Action] Checking JD approval, simulated user decision: {user_decision}")
    return {"approval_status": user_decision or "unclear"}

def submit_approval_node(state, **kwargs):
    print("[Action] JD Approved! Submitting...")
    return {"status": "submitted"}

def refine_jd_node(state, **kwargs):
    print("[Action] Refining JD as per requested changes...")
    return {"status": "refined"}

def handle_other_request(state, **kwargs):
    print("[Action] Handling unrelated request...")
    return {"status": "handled_other"}

def handle_unclear_intent(state, **kwargs):
    print("[Action] Handling unclear intent...")
    return {"status": "unclear_handled"}

def handle_exit(state, **kwargs):
    print("[Action] Exiting workflow...")
    return {"status": "exit"}


# ---------------------------
# Decision Functions (Independent)
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
# Create StateGraph Nodes (Loose Coupling)
# ---------------------------
nodes = {
    "start": StateNode("start", next_state="classify_intent"),

    "classify_intent": StateNode(
        "classify_intent",
        action=lambda state: classify_intent(state, state.get("user_input")),
        next_state=route_decision
    ),

    "check_jd_status": StateNode("check_jd_status", action=check_jd_status),

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
        action=lambda state: check_approval(state, state.get("user_decision")),
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

    "handle_exit": StateNode("handle_exit", action=handle_exit)
}


# ---------------------------
# Initialize StateGraph
# ---------------------------
workflow = StateGraph(nodes=nodes, start_state="start")


# ---------------------------
# Run Workflow (Loose Coupling)
# ---------------------------
def run_workflow(user_input, jd_exists=False, user_decision=None):
    initial_state = {
        "user_input": user_input,
        "jd_exists": jd_exists,
        "user_decision": user_decision
    }
    workflow.run(initial_state)


# ---------------------------
# Example Runs
# ---------------------------
print("=== Example 1: Resource Allocation, JD exists, approved ===")
run_workflow(user_input="resource_allocation", jd_exists=True, user_decision="approved")

print("\n=== Example 2: Other Request ===")
run_workflow(user_input="other")

print("\n=== Example 3: Resource Allocation, JD does not exist ===")
run_workflow(user_input="resource_allocation", jd_exists=False)
