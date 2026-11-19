ASK TUTOR — RESOURCE-AWARE AGENTIC UPGRADE (FIRST IMPLEMENTATION)

What is implemented:
- Coordinator + Progress/Planning roles run a deterministic observe/plan/act/evaluate loop after objective and written assessments.
- Per-learner JSON stores current recommended plans and an explainable decision history.
- Students can accept, skip or complete recommended plans; no automatic paid API calls.
- Progress page displays plans and agent decision traces.
- A subsequent assessment evaluates whether mastery improved after an accepted/completed plan.
- Existing TutorAgent, AssessmentAgent and PlannerAgent modules and existing generative tutor endpoints remain intact.
- All new endpoints require student authentication and learner ownership.

New API:
 GET /learner/{learner_id}/agent-state
 POST /learner/agent-plan/action {learner_id,subject,topic,action:accept|skip|complete}

To demonstrate: log in as a student, complete an objective assessment,
open Progress and press 'Refresh agent decisions'. Accept the plan,
complete another assessment on the same topic, and review the trace.

Scope and limitations:
- This is a functional first-stage rule-driven orchestration workflow, NOT a completed multi-agent research system.
- The current planner does not yet autonomously retrieve a prerequisite lesson or invoke a new tutoring/model tool when the plan is accepted.
- 'Mark complete' is student-reported, not independently verified.
- A mastery change is not proof of learning gain; formal evaluation is still required.
- Existing diagrams/illustrations remain. Dedicated diffusion image/video generation is NOT implemented.
- Existing offline Ollama capability depends on the user's hardware and installed model.
- Avoid claims of affordability without measured hardware, energy and per-student costs.

Existing test suite has two known unrelated failures (OCR health contract and planner subject coverage).

VISIBLE DASHBOARD PATCH: AI Learning Agent sidebar page and homepage card. Study/Practice buttons navigate to existing learning tools. No autonomous tool execution added in this patch.
