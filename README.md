# Agentic Personalised Learning — Working Prototype

This is a working, runnable proof-of-concept of the reference architecture described
in the accompanying paper/dissertation. It demonstrates: student signup/login,
geography- and stream-aware curriculum routing (Nigeria's JSS/SS system with
Science/Commercial/Arts streams, plus a Ghana proof-of-concept), and the core
tutoring loop — RAG-grounded explanation → practice question → scored answer →
persistent per-learner mastery update — using only free, local, open-source
components. No API key, no cloud bill, no internet dependency at inference time.

## What this proves (and what it deliberately does not attempt yet)

**Proves:**
- Full authentication: signup with hashed passwords (PBKDF2-HMAC-SHA256, per-user
  salt, via SQLite), login, and token-based session access to the dashboard
- Geography-aware curriculum: a student's registered country determines which
  classes and subjects they see. Nigeria (JSS 1, Primary 5, SS3) and Ghana (SHS3)
  are both live, non-overlapping, and independently filterable — proving the
  architecture genuinely generalises across countries, not just Nigeria
- Stream-aware subject offering for Nigerian senior secondary: a Science-stream
  SS3 student sees Biology (Science-only) + Mathematics (compulsory to all
  streams); a Commercial-stream student sees Financial Accounting + Mathematics;
  an Arts-stream student sees Literature-in-English + Mathematics. This was
  verified live: swapping the `stream` parameter genuinely changes what subjects
  are returned, confirmed by direct testing, not just claimed
- **A planner agent that builds a session plan spanning ALL of a learner's subjects**,
  prioritising whichever topics have the lowest mastery. Verified live through the
  real HTTP API: mastering one topic causes the very next plan request to drop it
  and surface the next-weakest topic instead. The topic-selection decision is fully
  deterministic and does not depend on the LLM being reachable (the plan still
  returns correctly, with a templated fallback introduction, when Ollama is down)
  — only the one-sentence friendly framing of the plan uses the LLM, and it is
  explicitly instructed not to introduce topics beyond the ones already selected
- Retrieval-augmented generation grounds the tutor's answers in actual curriculum
  content rather than open-ended generation (the paper's RQ4 — factual reliability)
- A learner's mastery is tracked per topic and persists across sessions
- The whole system runs on free, open-weight, locally-hosted infrastructure

- A **teacher-facing class overview** (`frontend/teacher.html`): a teacher selects
  country/class/stream and sees a summary-first view (total students, how many
  need attention, class average mastery) followed by a per-student drill-down
  with automatic "stuck" flags (low mastery despite 3+ genuine attempts, not
  just "hasn't started yet") and "inactive" flags (no activity, or none in the
  last 7 days). Verified live with three distinct real scenarios through the
  actual API: a thriving student (0 flags, correctly sorted last), a genuinely
  struggling student (correctly flagged "stuck" after 4 wrong attempts), and a
  never-logged-in student (correctly flagged "inactive") — all three flags and
  the aggregate class-average math confirmed correct against hand-computed
  expected values, not just eyeballed.

**Does not yet attempt** (intentionally out of scope for this build):
- Voice input/output (ASR/TTS)
- Offline mobile client / edge deployment — this runs as a web app for now
- Real computation/calculator tool — the tutor explains concepts from curriculum
  text; it does not yet reliably solve novel arithmetic problems (small local
  LLMs are unreliable at math; this needs a dedicated calculator tool, not RAG)
- Full curriculum coverage: Nigeria has sample content for Primary 5, JSS 1, and
  SS3 (one subject per stream, plus compulsory Mathematics) — not the complete
  WAEC syllabus. Ghana has one proof-of-concept subject (Integrated Science,
  SHS3) to demonstrate the multi-country architecture works, not full WASSCE
  coverage. Adding more countries or full subject coverage means adding more
  JSON files to `app/data/curriculum/` in the same format — no code changes
  needed, but real syllabus content must be sourced and verified by a subject
  expert before being added; this dissertation/prototype does not claim to have
  authored exam-accurate content beyond the samples listed above.
- Production-grade auth: session tokens are held in an in-memory dictionary
  (lost on server restart), with no expiry, no HTTPS, no CSRF protection.
  Password hashing itself is done correctly; session management is not
  production-ready and is flagged as such, not hidden.
- The teacher overview endpoint (`/teacher/overview`) has no teacher-specific
  authentication at all in this prototype — anyone who knows the URL can view
  any class's data by choosing filters. This is stated on the teacher page
  itself, not hidden, and is a concrete, named gap for a real deployment:
  a teacher/admin role needs to be added to the auth system before this view
  is exposed beyond a local demo.

## New in this update: verified computation (calculator tool)

Closes a real, previously-flagged gap: the tutor could explain *concepts*
from curriculum text but had no way to reliably *solve* a novel arithmetic
or algebra problem — and small local LLMs are genuinely unreliable at
arithmetic, so letting the LLM guess would have undermined the whole
anti-hallucination design.

- `app/agents/calculator_tool.py` uses **sympy** (safe symbolic parsing,
  not `eval()`) to compute a real, verified answer to arithmetic
  expressions and single-variable equations *before* the LLM is asked to
  explain anything. The LLM's job becomes explaining the steps to an
  already-known-correct answer, not inventing the answer itself — the
  arithmetic equivalent of RAG grounding.
- Verified against **12 tests**, including a safety test confirming
  malicious input cannot execute arbitrary code (sympy's parser is not
  `eval()`), and tests confirming purely conceptual questions ("what is a
  fraction", "explain genetics") correctly fall through to normal
  curriculum-retrieval tutoring rather than being misrouted.
- The `/ask` response now includes a `grounding_method` field
  (`"computation"` / `"retrieval"` / `"none"`) so it's always traceable
  *which* mechanism grounded a given answer — shown directly in the
  dashboard under each tutor response.
- Handles: basic arithmetic, fractions, percentages, exponents and
  logarithms (directly exercising the SS3 "Indices and Logarithms"
  curriculum topic), and single-variable linear equations. Does **not**
  attempt multi-variable systems or calculus — out of scope, and it says
  so (falls through to normal tutoring) rather than guessing.

## New in this update: real step-by-step working, shown on a visual board

Direct response to feedback that a paragraph of prose describing "how to
solve" a maths problem is not how mathematics is actually taught — a
teacher shows working, step by step, the way it would appear on a board.

- `calculator_tool.py` now generates genuine, mathematically-verified
  step-by-step working (not LLM-narrated prose) for its supported cases:
  linear equations (`"Subtract 5 from both sides: 2x = 10"`, with the
  correct verb — add vs. subtract — worked out from the actual sign of
  the constant term, not guessed), two-term fraction addition/subtraction
  (showing the common-denominator method), percentages, and small integer
  exponents (shown as repeated multiplication). A real bug was caught and
  fixed here during testing: the first version computed the "move this
  constant" step from the combined left-minus-right expression rather
  than the original left-hand side alone, which produced a
  mathematically-backwards instruction (e.g. told the student to *add*
  10 to both sides of `2x + 5 = 15`, instead of *subtract* 5) — caught by
  a test asserting the actual step text, not just that steps existed.
- These steps are rendered in the dashboard as an actual **chalkboard**
  visual — a dark board with a wooden frame, monospace "chalk" text, and
  the final answer highlighted, with each line revealing in sequence
  rather than all at once, echoing how a teacher writes one line at a
  time. Retrieval-grounded conceptual answers ("what is a fraction")
  still use plain prose, since a board doesn't make sense for those.
- **Reliability fix included**: previously, even though the correct
  answer was already computed, the whole response still failed if Ollama
  was unreachable, because the LLM call for the explanation wasn't
  wrapped defensively. Verified live through the real API with Ollama
  down: the full worked solution — all steps, correct final answer — is
  now returned regardless, with only the one-sentence friendly intro
  degrading to a simple fallback. This brings the tutor's computation
  path in line with the same offline-resilience principle already used
  in the planner agent.
- 4 new/updated tests assert the actual step *content* is correct (e.g.
  that `2x - 5 = 15` says "Add 5 to both sides", not "Subtract"), not
  just that some steps exist — this is what caught the bug above.

## New in this update: photo upload, voice, and language switching

- **Photo/file upload with OCR**: students can photograph handwritten work
  or upload an image; Tesseract OCR extracts the text into the question box.
  Tested against the real Tesseract engine (not mocked) — see `tests/test_ocr.py`.
  Requires the Tesseract OCR **engine** to be installed separately (see setup
  below) — `pip install pytesseract` alone is not enough, since pytesseract is
  only a wrapper that calls out to the real Tesseract binary.
- **Camera**: on a phone, the "Take photo" button opens the camera directly
  (via the HTML `capture` attribute). On a PC, it behaves the same as file
  upload — there is no separate "camera" feature on desktop, since a PC has
  no camera-app equivalent to hand a photo back from.
- **Voice input/output — English only**: uses the browser's own built-in
  speech recognition and speech synthesis (Chrome/Edge), no install needed.
  This is explicitly English-only. Voice for Yoruba/Igbo/Hausa etc. is **not**
  included, because no free, good-quality speech engine exists yet for most
  Nigerian languages — see the paper's RQ3. Building English-only voice and
  calling it "voice support" without that caveat would misrepresent what's
  actually solved versus what remains an open research gap.
- **UI language switching**: interface labels (buttons, headings, placeholders)
  can be switched between English, Yorùbá, Igbo, and Hausa via the dropdown
  in the dashboard header. **Important**: these translations are a good-faith
  attempt using common vocabulary, but have **not** been reviewed by a native
  speaker fluent in academic/educational register. Have someone verify them
  before using this with real students. This switches interface chrome only —
  it does not translate the tutor's actual explanations, which remain in
  English (see the "Tutor explanations in other languages" caveat below).



Verified against current WAEC subject-combination rules: three subjects
(English Language, Mathematics, Civic Education) are compulsory for every
senior secondary student regardless of stream; Science-stream students take
Physics/Chemistry/Biology-type subjects; Commercial-stream students take
Economics/Accounting-type subjects; Arts-stream students take
Literature/Government/History-type subjects. This prototype implements
Mathematics as the compulsory example and one representative subject per
stream (Biology/Financial Accounting/Literature-in-English) to demonstrate
the filtering logic correctly, not as a complete subject list.

## Architecture (maps directly to the paper's reference architecture)

```
signup.html / login.html --> app/auth.py (SQLite, hashed passwords, session tokens)
                                    |
dashboard.html  --calls-->  app/main.py (FastAPI, token-protected)
                                    |
                     +--------------+--------------+
                     |              |               |
             app/agents/     app/rag/         app/learner_model.py
             tutor_agent.py  retriever.py     (mastery per topic,
             assessment_     (TF-IDF search   JSON-file store)
             agent.py        + country/class/
                     |       subject/stream
                     |       filtering)
                     v
             app/llm_client.py
               (calls local Ollama --> open-weight model, e.g. llama3.2)
```

## One-time setup (on your own machine — this needs to run outside any sandbox)

### 1. Install Python dependencies
```bash
cd tutor-project
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Install Ollama and pull a model
Download from https://ollama.com/download, then:
```bash
ollama pull llama3.2:1b
```

### 3. Install the Tesseract OCR engine (required for photo upload)
`pip install pytesseract` (already in requirements.txt) only installs a
*wrapper* — the actual OCR engine is a separate program:
- **Windows**: download and run the installer from
  https://github.com/UB-Mannheim/tesseract/wiki (the UB-Mannheim build is the
  standard Windows distribution). During install, note the install path
  (default is usually `C:\Program Files\Tesseract-OCR`).
- If `pytesseract` can't find it after installing, add the install folder to
  your Windows PATH, or set it explicitly at the top of `app/ocr_service.py`:
  `pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"`

If this step is skipped, photo upload will fail with a clear "Tesseract OCR
engine is not installed" error rather than crashing silently — everything
else in the app works fine without it.

## Running it

**Terminal — start the backend:**
```bash
cd tutor-project
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

**Frontend:** Open `frontend/signup.html` in your browser (not index.html —
that was the pre-auth version; the auth-gated flow now starts at signup).

Try:
- Sign up as a country: **Nigeria**, class: **SS3**, stream: **Science**,
  academic goal: anything you like
- You'll land on the dashboard already scoped to your class/stream — ask
  "what is a fraction" or "explain genetics" and try a practice question
- Log out and sign up again as a **Commercial** or **Arts** stream student
  to see the subject list change accordingly
- Try country **Ghana**, class **SHS3** to see the second-country proof of concept

## Running the tests

```bash
python3 tests/test_retriever.py   # 10 tests: retrieval, country, stream filtering
python3 tests/test_learner_model.py  # 4 tests: mastery tracking
python3 tests/test_auth.py        # 7 tests: signup, login, hashing, sessions
python3 tests/test_planner.py     # 5 tests: session planning, cross-subject prioritisation, LLM-fallback
python3 tests/test_teacher_overview.py  # 8 tests: stuck/inactive flag logic, class summary stats
python3 tests/test_ocr.py         # 3 tests: OCR against the real Tesseract engine
python3 tests/test_calculator_tool.py     # 15 tests: safe computation, correct step narratives, injection safety
python3 tests/test_tutor_agent_routing.py # 7 tests: computation/retrieval/no-match routing, offline resilience

```

All 59 tests pass as of this build, verified by direct execution.

## Adding real curriculum content (including new countries)

Add a new JSON file to `app/data/curriculum/` with `country`, `class_level`,
`subject`, `topic`, optional `stream` (for senior-secondary-equivalent classes
with tracks), and a list of `chunks`. No code changes needed — the retriever
loads every JSON file automatically. To add a new country entirely, just use
that country's name as the `country` field and its own class-level naming
(e.g. Kenya's "Form 4", South Africa's "Grade 12") — the filtering logic is
already country-agnostic.


## Known limitations to disclose honestly

- TF-IDF retrieval (not neural embeddings) — chosen deliberately to avoid any
  model download for the retrieval step, keeping the whole system runnable
  with zero downloads beyond the one-time Ollama model pull. It works well for
  a small curriculum corpus; a larger real deployment should move to the
  sqlite-vec/Chroma approach described in the paper's Section 3.
- Small local models (1B–3B parameters) are noticeably weaker than large
  hosted models — expect occasionally clumsy phrasing. This is an honest
  reflection of the real cost/quality tradeoff the paper's architecture is
  built around, not a bug.
- Single-machine only — this is a development/demo setup, not the distributed,
  horizontally-scalable deployment described in the paper's cloud
  infrastructure layer.
