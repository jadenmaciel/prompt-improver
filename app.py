"""
Prompt Improver — local, offline Tkinter app.
Type a raw prompt, get an optimized prompt back for use with any AI tool.

Run: python3.12 app.py
"""

import platform
import re
import difflib
import tkinter as tk
from tkinter import messagebox

# ---------------------------------------------------------------------------
# Platform
# ---------------------------------------------------------------------------

_SYSTEM = platform.system()

# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------

C = {
    "bg":          "#141414",   # root window
    "panel_l":     "#1c1c1e",   # left panel
    "panel_r":     "#111111",   # right panel (slightly darker = output "canvas")
    "surface":     "#242424",   # raised surfaces (header bars, options bg)
    "surface2":    "#2a2a2a",   # slightly lighter surface (entry bg)
    "border":      "#2e2e2e",   # hairline borders
    "border_focus":"#4a90d9",   # focused border accent
    "text":        "#e2e2e2",   # primary text
    "text2":       "#888888",   # secondary / labels
    "muted":       "#444444",   # placeholder / disabled
    "accent":      "#4a90d9",   # blue accent
    "accent_hov":  "#5a9fd4",
    "ok":          "#3dd68c",   # green success
    "ok_dim":      "#0f2e1e",   # muted green bg
    "warn":        "#ff6b6b",   # red warning
    "warn_dim":    "#2e0f0f",   # muted red bg
    "btn_p":       "#4a90d9",   # primary button bg
    "btn_p_hov":   "#5a9fd4",
    "btn_p_fg":    "#ffffff",
    "btn_s":       "#2a2a2a",   # secondary button bg
    "btn_s_hov":   "#333333",
    "btn_s_fg":    "#c0c0c0",
    "scroll":      "#2e2e2e",   # scrollbar track
    "scroll_th":   "#444444",   # scrollbar thumb
    "scroll_hov":  "#555555",
    "sash":        "#2e2e2e",
}

# ---------------------------------------------------------------------------
# Fonts
# ---------------------------------------------------------------------------

if _SYSTEM == "Darwin":
    F = {
        "ui":      ("SF Pro Text",    12),
        "ui_b":    ("SF Pro Text",    12, "bold"),
        "sm":      ("SF Pro Text",    11),
        "sm_b":    ("SF Pro Text",    11, "bold"),
        "xs":      ("SF Pro Text",    10),
        "mono":    ("Menlo",          12),
        "mono_sm": ("Menlo",          10),
        "title":   ("SF Pro Display", 13, "bold"),
    }
elif _SYSTEM == "Windows":
    F = {
        "ui":      ("Segoe UI", 10),
        "ui_b":    ("Segoe UI", 10, "bold"),
        "sm":      ("Segoe UI", 9),
        "sm_b":    ("Segoe UI", 9, "bold"),
        "xs":      ("Segoe UI", 8),
        "mono":    ("Consolas", 10),
        "mono_sm": ("Consolas", 9),
        "title":   ("Segoe UI", 11, "bold"),
    }
else:
    F = {
        "ui":      ("DejaVu Sans", 10),
        "ui_b":    ("DejaVu Sans", 10, "bold"),
        "sm":      ("DejaVu Sans", 9),
        "sm_b":    ("DejaVu Sans", 9, "bold"),
        "xs":      ("DejaVu Sans", 8),
        "mono":    ("DejaVu Sans Mono", 10),
        "mono_sm": ("DejaVu Sans Mono", 9),
        "title":   ("DejaVu Sans", 11, "bold"),
    }

WINDOW_TITLE   = "Prompt Improver"
INITIAL_WIDTH  = 1160
INITIAL_HEIGHT = 760
MIN_WIDTH      = 900
MIN_HEIGHT     = 600

USAGE_NOTE = (
    "---\n"
    "Paste the prompt above into your AI tool of choice.\n"
    "Adjust any bracketed sections as needed."
)

# ---------------------------------------------------------------------------
# Knowledge bases for intelligent analysis
# ---------------------------------------------------------------------------

# Maps keyword → canonical display name
_TECH_TERMS: dict[str, str] = {
    # Protocols / standards
    "mcp": "Model Context Protocol (MCP)", "rest": "REST", "graphql": "GraphQL",
    "grpc": "gRPC", "websocket": "WebSockets", "oauth": "OAuth",
    "jwt": "JWT", "openapi": "OpenAPI",
    # AI / ML
    "llm": "LLMs", "gpt": "GPT", "claude": "Claude", "gemini": "Gemini",
    "langchain": "LangChain", "rag": "RAG", "embedding": "embeddings",
    "fine-tun": "fine-tuning", "transformer": "transformers",
    # Backend / infra
    "api": "APIs", "microservice": "microservices",
    "docker": "Docker", "kubernetes": "Kubernetes", "k8s": "Kubernetes",
    "terraform": "Terraform", "aws": "AWS", "gcp": "Google Cloud",
    "azure": "Azure", "lambda": "AWS Lambda", "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL", "mysql": "MySQL", "mongodb": "MongoDB",
    "redis": "Redis", "kafka": "Kafka", "rabbitmq": "RabbitMQ",
    "celery": "Celery", "nginx": "nginx", "fastapi": "FastAPI",
    "django": "Django", "flask": "Flask", "express": "Express.js",
    "node": "Node.js", "nodejs": "Node.js", "deno": "Deno",
    # Frontend
    "react": "React", "vue": "Vue.js", "angular": "Angular",
    "nextjs": "Next.js", "next.js": "Next.js", "svelte": "Svelte",
    "tailwind": "Tailwind CSS", "typescript": "TypeScript",
    # Languages
    "python": "Python", "javascript": "JavaScript", "rust": "Rust",
    "go": "Go", "golang": "Go", "java": "Java", "kotlin": "Kotlin",
    "swift": "Swift", "c++": "C++", "c#": "C#",
    # Services / platforms
    "youtube": "YouTube API", "github": "GitHub", "stripe": "Stripe",
    "openai": "OpenAI API", "anthropic": "Anthropic API",
    "supabase": "Supabase", "firebase": "Firebase", "vercel": "Vercel",
    "netlify": "Netlify", "heroku": "Heroku",
    # Security
    "auth": "authentication", "authn": "authentication",
    "authz": "authorization", "ssl": "SSL/TLS", "tls": "TLS",
    "encryption": "encryption",
}

# Domain → (role description, domain label)
_DOMAIN_ROLES: dict[str, tuple[str, str]] = {
    "backend":    ("an experienced backend engineer with expertise in server architecture, APIs, and distributed systems",
                   "backend engineering"),
    "frontend":   ("an expert frontend developer specializing in modern UI frameworks and user experience",
                   "frontend development"),
    "devops":     ("a senior DevOps/SRE engineer with deep expertise in cloud infrastructure, CI/CD, and reliability",
                   "DevOps and infrastructure"),
    "ai_ml":      ("an expert AI/ML engineer with deep knowledge of language models, prompt engineering, and ML systems",
                   "AI and machine learning"),
    "security":   ("a senior security engineer and penetration testing specialist",
                   "cybersecurity"),
    "data":       ("an expert data scientist and data engineer with strong analytical and visualization skills",
                   "data science and engineering"),
    "mobile":     ("an experienced mobile developer with expertise in iOS, Android, and cross-platform frameworks",
                   "mobile development"),
    "education":  ("an expert educator and tutor who explains complex topics clearly with examples and analogies",
                   "education and teaching"),
    "writing":    ("a professional writer and editor with expertise in clear, compelling communication",
                   "writing and content"),
    "finance": (
        "an experienced small-business and personal-finance coach who helps people "
        "plan side hustles, manage budgets, and optimize credit-card and rewards strategies",
        "personal finance and small business"
    ),
    "business":   ("a strategic business consultant with expertise in product, growth, and operations",
                   "business strategy"),
    "general":    ("a knowledgeable and thoughtful assistant",
                   "general"),
}

# Task type → role activity modifier (used by _synthesize_role)
_TASK_ROLE_MODIFIERS: dict[str, str] = {
    "build":   "who architects and builds production-quality solutions",
    "design":  "who designs systems and creates technical blueprints",
    "explain": "who explains complex topics clearly with concrete examples",
    "compare": "who evaluates trade-offs and provides clear recommendations",
    "fix":     "who diagnoses and resolves issues systematically",
    "analyze": "who performs thorough analysis and identifies improvements",
    "write":   "who writes clear, polished, audience-appropriate content",
    "list":    "who provides comprehensive, well-organized information",
}

# Niche patterns: regex on core_subject → niche expertise string
_NICHE_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\bscrap", re.I),              "web scraping and data extraction"),
    (re.compile(r"\brate.?limit", re.I),        "API rate limiting and throttling"),
    (re.compile(r"\bcrawl", re.I),              "web crawling and indexing"),
    (re.compile(r"\bauth(?:entication|orization)?\b", re.I), "authentication and access control"),
    (re.compile(r"\bchat.?bot\b", re.I),        "conversational AI and chatbot design"),
    (re.compile(r"\breal.?time\b", re.I),       "real-time systems and event streaming"),
    (re.compile(r"\bcach(?:e|ing)\b", re.I),    "caching strategies and performance"),
    (re.compile(r"\btest(?:ing|s)?\b", re.I),   "testing strategies and quality assurance"),
    (re.compile(r"\bperformance\b", re.I),      "performance optimization and profiling"),
    (re.compile(r"\bmigrat", re.I),             "data migration and schema evolution"),
    (re.compile(r"\bgame\b", re.I),             "game logic and interactive systems"),
    (re.compile(r"\bpayment\b", re.I),          "payment processing and financial integrations"),
    (re.compile(r"\bsearch\b", re.I),           "search systems and information retrieval"),
    (re.compile(r"\bnotif", re.I),              "notification systems and messaging"),
    (re.compile(r"\bmonitor", re.I),            "monitoring, alerting, and observability"),
    (re.compile(r"\bCLI\b|command.?line", re.I), "command-line tools and terminal interfaces"),
    (re.compile(r"\bAPI\b", re.I),              "API design and integration"),
    (re.compile(r"\bdashboard\b", re.I),        "data visualization and dashboard design"),
    (re.compile(r"\bpipeline\b", re.I),         "data pipelines and workflow orchestration"),
    (re.compile(r"\boptimiz", re.I),            "optimization and efficiency improvements"),
]

# Task type → reasoning guidance injected into [TASK] section
_REASONING_GUIDANCE: dict[str, str] = {
    "build":   "Think through this systematically: requirements first, then architecture, then implementation details.",
    "design":  "Think through this systematically: clarify goals, explore options, evaluate trade-offs, then recommend.",
    "fix":     "Before proposing a fix, reason through the possible root causes and rule them out one by one.",
    "analyze": "Work through this methodically: gather observations, identify patterns, then form conclusions.",
    "compare": "Evaluate each option against the same criteria before making a recommendation.",
}

# Stronger fallback constraints (replaces the weak "Be specific and actionable")
_STRONGER_DEFAULTS: list[str] = [
    "Provide concrete examples, not abstract descriptions.",
    "If you are unsure about something, say so rather than guessing.",
    "Focus on practical, immediately actionable advice.",
    "Before finalizing, verify your answer is internally consistent and complete.",
]

# Domain detection: keyword → domain key
_DOMAIN_SIGNALS: list[tuple[str, str]] = [
    # ai_ml first — high priority
    ("mcp",         "backend"),
    ("llm",         "ai_ml"), ("gpt",         "ai_ml"), ("claude",      "ai_ml"),
    ("gemini",      "ai_ml"), ("langchain",    "ai_ml"), ("rag",         "ai_ml"),
    ("embedding",   "ai_ml"), ("fine-tun",     "ai_ml"), ("transformer", "ai_ml"),
    ("openai",      "ai_ml"), ("anthropic",    "ai_ml"),
    # backend
    ("server",      "backend"), ("api",         "backend"), ("endpoint",    "backend"),
    ("postgres",    "backend"), ("postgresql",  "backend"), ("mongodb",     "backend"),
    ("mysql",       "backend"), ("redis",       "backend"), ("kafka",       "backend"),
    ("supabase",    "backend"), ("firebase",    "backend"),
    ("microservice","backend"), ("database",    "backend"), ("backend",     "backend"),
    ("fastapi",     "backend"), ("django",      "backend"), ("flask",       "backend"),
    ("express",     "backend"), ("node",        "backend"), ("grpc",        "backend"),
    ("rest",        "backend"), ("graphql",     "backend"), ("websocket",   "backend"),
    # devops
    ("docker",      "devops"),  ("kubernetes",  "devops"),  ("k8s",         "devops"),
    ("terraform",   "devops"),  ("aws",         "devops"),  ("gcp",         "devops"),
    ("azure",       "devops"),  ("ci/cd",       "devops"),  ("pipeline",    "devops"),
    ("deploy",      "devops"),  ("nginx",       "devops"),  ("lambda",      "devops"),
    # frontend
    ("react",       "frontend"),("vue",         "frontend"),("angular",     "frontend"),
    ("frontend",    "frontend"),("nextjs",      "frontend"),("next.js",     "frontend"),
    ("svelte",      "frontend"),("tailwind",    "frontend"),("css",         "frontend"),
    ("ui",          "frontend"),("component",   "frontend"),
    # security
    ("security",    "security"),("auth",        "security"),("oauth",       "security"),
    ("jwt",         "security"),("encryption",  "security"),("vulnerability","security"),
    ("penetration", "security"),
    # data
    ("data",        "data"),    ("dataset",     "data"),    ("ml",          "data"),
    ("model",       "data"),    ("training",    "data"),    ("analysis",    "data"),
    ("visualization","data"),   ("pandas",      "data"),    ("sql",         "data"),
    # mobile
    ("ios",         "mobile"),  ("android",     "mobile"),  ("swift",       "mobile"),
    ("kotlin",      "mobile"),  ("react native","mobile"),  ("flutter",     "mobile"),
    ("expo",        "mobile"),
    # education
    ("study",       "education"),("explain",    "education"),("teach",      "education"),
    ("tutor",       "education"),("quiz",       "education"),("exam",       "education"),
    ("learn",       "education"),("course",     "education"),
    # writing
    ("essay",       "writing"), ("blog",        "writing"), ("article",     "writing"),
    ("content",     "writing"), ("story",       "writing"), ("copywriting", "writing"),
    # finance (cluster has more finance-specific keywords than business cluster, so finance wins count-based ties)
    ("finances",        "finance"), ("budget",         "finance"), ("spending",      "finance"),
    ("income",          "finance"), ("expenses",       "finance"), ("cash flow",     "finance"),
    ("credit card",     "finance"), ("amex",           "finance"), ("visa card",     "finance"),
    ("mastercard",      "finance"), ("apr",            "finance"), ("points",        "finance"),
    ("miles",           "finance"), ("rewards card",   "finance"), ("signup bonus",  "finance"),
    ("side hustle",     "finance"), ("vending",        "finance"), ("net worth",     "finance"),
    ("savings account", "finance"), ("student loan",   "finance"), ("credit limit",  "finance"),
    # business
    ("strategy",    "business"),("marketing",   "business"),("revenue",     "business"),
    ("startup",     "business"),("growth",      "business"),("product",     "business"),
]

# Task verb classification
_BUILD_RE    = re.compile(r"\b(make|build|create|implement|develop|code|set up|scaffold)\b", re.I)
_DESIGN_RE   = re.compile(r"\b(design|architect|plan|structure|outline|sketch)\b", re.I)
_EXPLAIN_RE  = re.compile(r"\b(explain|describe|what is|how does|how do|teach me|show me|help me understand|clarify)\b", re.I)
_COMPARE_RE  = re.compile(r"\b(compare|versus|vs\.?|difference between|which is better|pros and cons)\b", re.I)
_FIX_RE      = re.compile(r"\b(fix|debug|solve|troubleshoot|why (is|does|isn't|doesn't)|error|bug|broken|not working)\b", re.I)
_ANALYZE_RE  = re.compile(
    r"\b(check|look at|look through|look throughout|look over|look around|look into|"
    r"go through|examine|inspect|"
    r"analyze|analyse|review|audit|evaluate|assess|critique|improve my|optimize)\b",
    re.I
)
_WRITE_RE    = re.compile(r"\b(write|draft|generate|compose|craft)\b", re.I)
_LIST_RE     = re.compile(r"\b(list|enumerate|give me|show me|what are the)\b", re.I)

# Existing structural detection
_ROLE_PAT  = re.compile(r"\b(you are|act as|pretend(?: to be)?|as a|assume the role)\b", re.I)
_CTX_PAT   = re.compile(r"\b(context|background|given that|in this scenario|for this task|the situation is|here is the)\b", re.I)
_FMT_PAT   = re.compile(r"\b(json|markdown|table|bullet|bulleted|list|format|schema|html|csv|numbered|step[- ]by[- ]step|in a (?:table|list|chart))\b", re.I)
_CON_PAT   = re.compile(r"\b(don'?t|avoid|must|limit|max|only|no more than|keep it|without|exclude|do not|refrain|less than|at most)\b", re.I)
_SENT_RE   = re.compile(r"(?<=[.!?])\s+")
_ACRONYM_RE = re.compile(r"\b[A-Z]{2,5}\b")

_REQUEST_RE = re.compile(
    r'^\s*(?:(?:first|also|additionally|furthermore|second|finally|lastly)[,\s]+)?'
    r'(?:please\s+)?(what|how|why|when|can you|could you|help me|i need|i want|'
    r'tell me|look at|review|summarize|list|analyze|build|plan|check|explain|find|'
    r'show|give|create|make|write|compare|evaluate|assess)\b',
    re.I
)

_CHECKLIST_PAT = re.compile(
    r"\b(checklist|check list|action items)\b", re.I
)

_ARTIFACT_RE = re.compile(
    r"\b(project|repo|repository|codebase|code base|my code|the code|"
    r"this file|my files|source code|the app|my app|the script)\b",
    re.I
)

_MULTITASK_SECTION3: dict[str, str] = {
    "finance":   "Financial review (card details, budget, key numbers)",
    "business":  "Business analysis (market, operations, strategy)",
    "backend":   "Technical review (architecture, APIs, data layer)",
    "frontend":  "UI/UX review (components, performance, accessibility)",
    "devops":    "Infrastructure review (deployment, reliability, costs)",
    "ai_ml":     "Model and data review (approach, evaluation, risks)",
    "security":  "Security review (threats, vulnerabilities, mitigations)",
    "data":      "Data review (sources, quality, pipeline)",
    "mobile":    "Platform review (iOS/Android, performance, UX)",
    "education": "Learning path review (resources, milestones, gaps)",
    "writing":   "Content review (tone, structure, audience fit)",
    "general":   "Deep dive on each subtopic",
}

# Used by _constraints() for fact vs. directive classification
_FACT_RE      = re.compile(r'[$\d]')
_FACT_NOUN_RE = re.compile(r'\b(limit|points|month|week|spend|miles|reward|budget|income|apr|bonus)\b', re.I)
_DIRECTIVE_RE = re.compile(r"\b(must|should|don'?t|do not|avoid|only|no more than|please don'?t|refrain|exclude|keep it|limit to)\b", re.I)

# ---------------------------------------------------------------------------
# PromptAnalyzer  — extracts rich intent from raw text
# ---------------------------------------------------------------------------

class PromptAnalyzer:
    def analyze(self, raw: str) -> dict:
        t = raw.strip()
        w = t.split()
        tl = t.lower()

        task_type   = self._task_type(t)
        domains     = self._domains(tl)
        tech_stack  = self._tech_stack(tl)
        is_technical = (
            bool(tech_stack) or
            bool(_ACRONYM_RE.findall(t)) or
            domains[0] in ("backend","devops","frontend","ai_ml","security","data","mobile")
            if domains else False
        )

        summary, key_facts, norm_sents = self._summarize(raw)
        multi_task, task_sentences = self._detect_tasks(norm_sents)

        return {
            # Structural presence flags (used by badge display)
            "has_role":          bool(_ROLE_PAT.search(t)),
            "has_context":       bool(_CTX_PAT.search(t)),
            "has_task":          bool(task_type != "general"),
            "has_output_format": bool(_FMT_PAT.search(t)),
            "has_constraints":   bool(_CON_PAT.search(t)),
            # Rich intent
            "task_type":    task_type,       # build|design|explain|compare|fix|analyze|write|list|general
            "domains":      domains,         # ordered list of detected domains
            "tech_stack":   tech_stack,      # list of canonical tech names
            "is_technical": is_technical,
            # Helpers
            "is_short":     len(w) < 10,
            "is_long":      len(t) > 2000,
            "core_subject": self._core_subject(t),
            # Summarization & multi-task
            "summary":        summary,
            "key_facts":      key_facts,
            "multi_task":     multi_task,
            "task_sentences": task_sentences,
        }

    def _task_type(self, text: str) -> str:
        if _FIX_RE.search(text):    return "fix"
        if _COMPARE_RE.search(text): return "compare"
        if _ANALYZE_RE.search(text): return "analyze"
        if _BUILD_RE.search(text):   return "build"
        if _DESIGN_RE.search(text):  return "design"
        if _WRITE_RE.search(text):   return "write"
        if _EXPLAIN_RE.search(text): return "explain"
        if _LIST_RE.search(text):    return "list"
        return "general"

    def _domains(self, tl: str) -> list[str]:
        counts: dict[str, int] = {}
        for kw, domain in _DOMAIN_SIGNALS:
            if kw in tl:
                counts[domain] = counts.get(domain, 0) + 1
        if not counts:
            return ["general"]
        return sorted(counts, key=lambda k: -counts[k])

    def _tech_stack(self, tl: str) -> list[str]:
        seen: list[str] = []
        for kw, display in _TECH_TERMS.items():
            # Use word-boundary match to avoid "go" inside "mongo", etc.
            pattern = r"\b" + re.escape(kw) + r"\b"
            if re.search(pattern, tl) and display not in seen:
                seen.append(display)
        return seen

    def _core_subject(self, text: str) -> str:
        """Best-effort extraction of the main subject phrase."""
        # Strip leading filler / vague imperative verbs (multi-word phrases first)
        cleaned = re.sub(
            r"^(?:(?:take\s+a\s+look\s+at|look\s+(?:at|through(?:out)?|over|around|into)|"
            r"tell\s+me\s+about|show\s+me|find\s+out|figure\s+out|go\s+through)\s+|"
            r"(?:make|build|create|design|write|explain|compare|fix|debug|"
            r"analyze|analyse|help\s+me|can\s+you|please|i\s+want\s+to|i\s+need\s+to|"
            r"check|see|review|examine|inspect)\s+)",
            "", text.strip(), flags=re.I,
        )
        # Take up to first sentence or 120 chars
        first = _SENT_RE.split(cleaned)[0].strip()
        return first[:120]

    def _summarize(self, raw: str) -> tuple[str, list[str], list[str]]:
        """Clean, deduplicate, and summarize a raw prompt.

        Returns:
            summary_text: Up to 4 best sentences joined with a space.
            key_facts: Numeric/currency sentences not already in the summary.
            normalized_sentences: All deduplicated normalized sentences (for _detect_tasks).
        """
        # Step 1: Sentence split using existing module-level _SENT_RE
        raw_sents = [s.strip() for s in _SENT_RE.split(raw) if s.strip()]
        if not raw_sents:
            return raw.strip(), [], []

        # Step 2: Normalize each sentence
        normalized: list[str] = []
        for s in raw_sents:
            s = re.sub(r' {2,}', ' ', s)                             # collapse spaces
            s = re.sub(r'\.\.+', '.', s)                             # fix ".."
            s = re.sub(r',,+', ',', s)                               # fix ",,"
            s = re.sub(r'\b(\w+)\s+\1\b', r'\1', s, flags=re.I)     # "the the" → "the"
            s = s.strip()
            if s:
                normalized.append(s)

        # Step 3: Deduplicate — keep sentences with similarity ≤ 0.85 vs all already kept
        kept: list[str] = []
        for s in normalized:
            is_dupe = any(
                difflib.SequenceMatcher(None, s.lower(), k.lower()).ratio() > 0.85
                for k in kept
            )
            if not is_dupe:
                kept.append(s)

        # Step 4: Select up to 4 summary sentences (~400 char budget)
        # Both list (order) and set (O(1) dedup across priority passes)
        selected: list[str] = []
        selected_set: set[str] = set()

        def _add(s: str) -> bool:
            """Add s if not already selected and budget not exhausted."""
            if s in selected_set:
                return False
            if len(selected) >= 4 or sum(len(x) for x in selected) >= 400:
                return False
            selected.append(s)
            selected_set.add(s)
            return True

        # P1: Always include first sentence
        if kept:
            _add(kept[0])

        # P2: One numeric/currency sentence (save remaining for key_facts)
        _kf_re = re.compile(
            r'\$\d|[\d,]+\s*(point|limit|month|week|spend|mile|reward|apr|bonus)',
            re.I
        )
        numeric_added = 0
        for s in kept:
            if numeric_added >= 1:
                break
            if re.search(r'[$\d]', s) and _add(s):
                numeric_added += 1

        # P3: Sentences containing any domain keyword (skip key-fact sentences)
        domain_kws = {kw for kw, _ in _DOMAIN_SIGNALS}
        for s in kept:
            if _kf_re.search(s):
                continue
            if any(kw in s.lower() for kw in domain_kws):
                _add(s)

        # P4: Fill remaining slots with any kept sentence in order (skip key-fact sentences)
        for s in kept:
            if not _kf_re.search(s):
                _add(s)

        summary_text = " ".join(selected)

        # Step 5: Key facts — numeric sentences NOT already in the summary
        key_facts = [s for s in kept if _kf_re.search(s) and s not in selected_set]

        return summary_text, key_facts, kept

    def _detect_tasks(self, sents: list[str]) -> tuple[bool, list[str]]:
        """Detect whether sents represent multiple distinct requests.

        Returns:
            multi_task: True if 2+ request sentences detected.
            task_sentences: Up to 5 sentences that look like requests.
        """
        task_sents = [s for s in sents if _REQUEST_RE.search(s)]
        task_sents = task_sents[:5]
        multi_task = len(task_sents) >= 2
        return multi_task, task_sents

# ---------------------------------------------------------------------------
# PromptBuilder  — constructs a genuinely improved, specific prompt
# ---------------------------------------------------------------------------

# Maps user shorthand → expanded output format description
_FMT_EXPANSIONS: dict[str, str] = {
    "bullet":   "Bullet points, grouped into logical sections with a brief header per group.",
    "bullets":  "Bullet points, grouped into logical sections with a brief header per group.",
    "json":     "Valid JSON. Use a top-level key per section; arrays for lists of items.",
    "table":    "Markdown table. Choose column headers that best capture the relevant dimensions.",
    "markdown": "Markdown with ## section headers, bullet points where appropriate, and fenced code blocks for any code.",
    "prose":    "Clear, well-structured prose with short paragraphs and headers where the topic shifts.",
    "numbered": "Numbered list. Each item should be a complete sentence or short paragraph.",
    "code":     "A complete, runnable code block with inline comments on non-obvious lines.",
    "outline":  "A hierarchical outline using headings and indented sub-bullets.",
    "steps":    "Numbered step-by-step instructions. Each step is a single, concrete action.",
    "step":     "Numbered step-by-step instructions. Each step is a single, concrete action.",
    "summary":  "A concise executive summary: 3–5 bullet points covering the key points.",
    "checklist": "A prioritized actionable checklist using Markdown task boxes [ ].",
}


class PromptBuilder:

    def build(self, raw: str, analysis: dict, meta: dict) -> str:
        model  = meta.get("model",      "").strip()
        aud    = meta.get("audience",   "").strip()
        fmt    = meta.get("output_fmt", "").strip()
        tone   = meta.get("tone",       "").strip()
        mode   = meta.get("mode",       "").strip().lower()

        # Intent-based checklist override — takes priority over dropdown selection
        if _CHECKLIST_PAT.search(raw):
            fmt = "checklist"

        # Infer mode from is_technical when not explicitly provided
        if mode not in ("coding", "general"):
            mode = "coding" if analysis.get("is_technical") else "general"

        # Accumulate sections as (display_header, xml_tag, content) tuples
        sec_tuples: list[tuple[str, str, str]] = []

        # Always include role — either synthesized or acknowledging user's existing role
        sec_tuples.append(("ROLE / PERSONA", "role", self._role(analysis, model)))
        sec_tuples.append(("CONTEXT", "context", self._context(raw, analysis, aud)))
        sec_tuples.append(("TASK", "task", self._task(raw, analysis, mode)))

        inp = self._input_desc(raw, analysis)
        if inp:
            sec_tuples.append(("INPUT", "input", inp))

        sec_tuples.append(("OUTPUT FORMAT", "output_format", self._format(analysis, fmt, mode, raw)))

        examples = self._examples(analysis)
        if examples:
            sec_tuples.append(("EXAMPLES & DEMONSTRATION", "examples", examples))

        sec_tuples.append(("CONSTRAINTS & STYLE", "constraints", self._constraints(raw, analysis, tone, mode)))

        # Format sections — XML tags for Claude, bracket headers otherwise
        use_xml = "claude" in model.lower() if model else False
        if use_xml:
            body = "\n\n".join(f"<{tag}>\n{content}\n</{tag}>" for _, tag, content in sec_tuples)
        else:
            body = "\n\n".join(f"[{header}]\n{content}" for header, _, content in sec_tuples)
        if analysis.get("is_long"):
            summary_len = len(analysis.get("summary", ""))
            if summary_len < len(raw.strip()) * 0.4:
                body += "\n\n⚠ Original prompt was very long; key points were summarized above."
        # Final cleanup: remove double periods and collapse extra spaces
        body = re.sub(r'\.\.+', '.', body)
        body = re.sub(r' {2,}', ' ', body)
        return body

    # ── Role ──────────────────────────────────────────────────────────

    def _role(self, a: dict, model: str) -> str:
        if a["has_role"]:
            return "(role already specified in your prompt — preserved as-is)"

        role_desc = self._synthesize_role(a)
        suffix = f", optimized for use with {model}" if model else ""
        return f"You are {role_desc}{suffix}."

    def _synthesize_role(self, a: dict) -> str:
        """Build a specific role from domain + task_type + tech_stack + subject niche."""
        primary_domain = a["domains"][0] if a["domains"] else "general"
        task_type = a.get("task_type", "general")
        tech = a.get("tech_stack", [])
        subject = a.get("core_subject", "")

        _, domain_label = _DOMAIN_ROLES.get(primary_domain, _DOMAIN_ROLES["general"])
        task_mod = _TASK_ROLE_MODIFIERS.get(task_type, "")

        # Build the role description in layers
        if primary_domain == "general" and not tech and task_type == "general":
            # Truly generic prompt — use simple fallback
            return _DOMAIN_ROLES["general"][0]

        # Base: "a senior {domain} specialist {task_modifier}"
        if task_mod:
            role = f"a senior {domain_label} specialist {task_mod}"
        else:
            # No task modifier — fall back to domain role description
            role = _DOMAIN_ROLES.get(primary_domain, _DOMAIN_ROLES["general"])[0]

        # Tech specialization
        if tech and primary_domain not in ("education", "writing", "business", "general"):
            tech_str = ", ".join(tech[:3])
            role += f", with deep expertise in {tech_str}"

        # Niche from core_subject
        if subject:
            for pat, niche in _NICHE_PATTERNS:
                if pat.search(subject):
                    # Avoid redundancy with tech stack
                    if not any(t.lower() in niche.lower() for t in tech):
                        role += f" and specific experience with {niche}"
                    break

        return role

    # ── Context ───────────────────────────────────────────────────────

    def _context(self, raw: str, a: dict, aud: str) -> str:
        lines = []

        # 1. Structured goal line — never echoes raw input verbatim
        subject = self._clean(self._clean_subject(raw, a))
        if a.get("multi_task"):
            lines.append(f"Working on: {subject} \u2014 across multiple related goals.")
        else:
            verb_map = {
                "build":   "build",    "design":  "design",  "explain": "understand",
                "compare": "evaluate", "fix":     "fix",      "analyze": "analyze",
                "write":   "write",    "list":    "list",
            }
            verb = verb_map.get(a["task_type"], "work on")
            lines.append(f"The goal is to {verb}: {subject}.")
        if a.get("key_facts"):
            lines.append("Key details: " + " ".join(a["key_facts"]))
        else:
            # Numeric facts may be in summary (not key_facts) for short prompts.
            # Surface them here so important numbers never disappear from context.
            summary_sents = [s.strip() for s in (a.get("summary") or "").split(". ") if s.strip()]
            fact_sents = [
                s for s in summary_sents
                if _FACT_RE.search(s) and _FACT_NOUN_RE.search(s)
                and re.sub(r'[.!?,;:]+$', '', s.strip()) != subject
            ]
            if fact_sents:
                lines.append("Key details: " + " ".join(fact_sents[:2]))

        # 2. Domain context — label only, subject is already in the goal line
        domain = a["domains"][0] if a["domains"] else "general"
        if domain != "general":
            _, domain_label = _DOMAIN_ROLES.get(domain, _DOMAIN_ROLES["general"])
            lines.append(f"Domain: {domain_label}.")

        # 3. Call out specific technologies so the AI focuses on them
        tech = a.get("tech_stack", [])
        if tech:
            lines.append(f"Key technologies involved: {', '.join(tech[:5])}.")

        # 4. Audience
        if aud:
            lines.append(f"Target audience: {aud}.")
        elif domain in ("finance", "business"):
            lines.append("Assume a non-technical business owner audience — plain language, no jargon.")
        elif a["is_technical"]:
            lines.append("Assume a technical developer audience familiar with the relevant concepts.")
        else:
            lines.append("Assume a general audience — avoid unnecessary jargon.")

        # 5. Variable injection — prompt AI to ask for external artifacts if not in context
        if _ARTIFACT_RE.search(raw):
            lines.append(
                "Note: If the relevant code, files, or repository path are not already "
                "in your context, ask the user to provide them before proceeding."
            )

        return "\n".join(lines)

    # ── Task ──────────────────────────────────────────────────────────

    # Verbs that signal analysis intent even when task_type was mis-detected
    _STRONG_ANALYZE_VERB_RE = re.compile(
        r"^(?:look\s+\w+\s+|analyze\s+|analyse\s+|review\s+|examine\s+|inspect\s+|"
        r"check\s+|assess\s+|evaluate\s+|audit\s+|investigate\s+|explore\s+|research\s+)",
        re.I
    )

    def _task(self, raw: str, a: dict, mode: str = "coding") -> str:
        if a.get("multi_task"):
            task_sents = list(a.get("task_sentences", []))
            if task_sents:  # Guard: fall through to single template if list is empty
                # Auto-inject finance review when facts exist but no finance task was requested
                _fin_kws = ("amex", "card", "financ", "credit", "point", "limit", "budget")
                domain = a["domains"][0] if a["domains"] else "general"
                has_finance_task = any(
                    kw in s.lower() for s in task_sents for kw in _fin_kws
                )
                # Check raw prompt directly — numeric facts may be in summary, not key_facts
                raw_sents = [s.strip() for s in _SENT_RE.split(raw) if s.strip()]
                has_finance_facts = any(
                    _FACT_RE.search(s) and _FACT_NOUN_RE.search(s) for s in raw_sents
                )
                if domain == "finance" and has_finance_facts and not has_finance_task:
                    task_sents.append(
                        "Review the financial details (card limits, points, spending targets)"
                        " and explain how they connect to the overall plan."
                    )
                def _clean_task(s: str) -> str:
                    s = re.sub(r'^(?:(?:first|also|additionally|second|finally|lastly)[,\s]+)?please\s+', '', s.strip(), flags=re.I)
                    return (s[0].upper() + s[1:]) if s else s
                numbered = "\n".join(
                    f"{i+1}. {_clean_task(s).rstrip('.')}."
                    for i, s in enumerate(task_sents)
                )
                return "Address each of the following systematically:\n" + numbered

        subject   = self._clean(self._clean_subject(raw, a))
        task_type = a["task_type"]

        # Verb-replacement guard: if subject still starts with a strong analyze-class verb
        # (e.g. _core_subject missed "look throughout"), reroute to analyze and strip the verb.
        if task_type not in ("analyze", "fix") and self._STRONG_ANALYZE_VERB_RE.match(subject):
            subject   = self._clean(self._STRONG_ANALYZE_VERB_RE.sub("", subject).strip())
            task_type = "analyze"

        tech      = a.get("tech_stack", [])
        # Only add tech suffix if none of the tech items are already in the subject
        subject_lower = subject.lower()
        novel_tech = [t for t in tech[:2] if t.lower() not in subject_lower]
        tech_str  = f" using {', '.join(novel_tech)}" if novel_tech else ""

        # Mode-aware analyze cover points
        if mode == "general":
            analyze_cover = (
                "Cover: (1) strategic objectives and what success looks like, "
                "(2) logic gaps or missing pieces, "
                "(3) immediate action items."
            )
        else:
            analyze_cover = (
                "Cover: (1) current state and what's working, "
                "(2) issues, gaps, or risks identified, "
                "(3) specific actionable recommendations, "
                "(4) priority order for improvements."
            )

        # Mode-aware build cover points
        if mode == "general":
            build_cover = (
                "Cover: (1) strategic objectives and requirements, "
                "(2) logical flow and component responsibilities, "
                "(3) potential gaps or risks."
            )
        else:
            build_cover = (
                "Cover: (1) overall architecture and how components fit together, "
                "(2) step-by-step implementation with concrete code examples, "
                "(3) error handling and edge cases."
            )

        expansions = {
            "build": (
                f"Design and implement {subject}{tech_str}.\n"
                f"{build_cover}"
            ),
            "design": (
                f"Design {subject}{tech_str}.\n"
                f"Cover: (1) high-level architecture and component breakdown, "
                f"(2) key design decisions and trade-offs, "
                f"(3) how you would implement this in practice."
            ),
            "explain": (
                f"Explain {subject} clearly and thoroughly.\n"
                f"Cover: (1) what it is and why it matters, "
                f"(2) how it works step by step, "
                f"(3) a practical example or analogy, "
                f"(4) common pitfalls or misconceptions."
            ),
            "compare": (
                f"Compare {subject}.\n"
                f"Cover: (1) key similarities and differences, "
                f"(2) pros and cons of each option, "
                f"(3) when to use which, "
                f"(4) a clear recommendation with reasoning."
            ),
            "fix": (
                f"Diagnose and fix: {subject}.\n"
                f"Cover: (1) likely root causes, "
                f"(2) step-by-step debugging approach, "
                f"(3) the fix with code if applicable, "
                f"(4) how to prevent this in future."
            ),
            "analyze": (
                f"Analyze {subject}.\n"
                f"{analyze_cover}"
            ),
            "write": (
                f"Write {subject}.\n"
                f"The output should be polished, complete, and ready to use. "
                f"Match the tone and style to the intended audience and purpose."
            ),
            "list": (
                f"List {subject}.\n"
                f"Be comprehensive and specific — include brief explanations for each item, "
                f"not just bare names."
            ),
        }

        if task_type in expansions:
            result = expansions[task_type]
            guidance = _REASONING_GUIDANCE.get(task_type)
            if guidance:
                result += f"\n\n{guidance}"
            # Suggest decomposition for complex single tasks
            is_complex = (
                task_type in ("build", "design")
                and (len(a.get("tech_stack", [])) >= 2 or not a.get("is_short"))
                and not a.get("multi_task")
            )
            if is_complex:
                result += "\n\nBreak your response into clearly labeled phases or steps."
            return result

        # Fallback: use the core subject with light expansion
        return f"{raw.strip()}\n\nBe specific, thorough, and practical in your response."

    # ── Input description ─────────────────────────────────────────────

    def _input_desc(self, raw: str, a: dict) -> str:
        task_type = a["task_type"]
        if re.search(r"\b(the following|below|provided|given|above)\b", raw, re.I):
            return "The user will paste or attach relevant content (code, text, data, etc.) below this prompt."
        if task_type == "fix":
            return ("The user will provide: the relevant code snippet, error message, or description "
                    "of the unexpected behavior.")
        if task_type == "analyze":
            return "The user will provide: the content, code, or system to be analyzed."
        return ""

    # ── Examples & demonstration ──────────────────────────────────────

    def _examples(self, a: dict) -> str:
        """Return task-type-specific guidance on examples/demonstration."""
        examples_map = {
            "build": (
                "Show a minimal working example first, then build up to the full implementation.\n"
                "Structure each component as: purpose \u2192 implementation \u2192 usage example."
            ),
            "write": (
                "Include a brief example of the desired tone and style before writing the full piece."
            ),
            "explain": (
                "Include at least one concrete example or analogy to ground the explanation.\n"
                "For each concept: define it \u2192 show how it works \u2192 show when to use it."
            ),
            "fix": (
                "Show the corrected code alongside the original so the difference is clear.\n"
                "For each fix: problem \u2192 root cause \u2192 solution \u2192 verification."
            ),
            "compare": (
                "Include a concrete scenario where each option excels to illustrate the trade-offs.\n"
                "For each option: strengths \u2192 weaknesses \u2192 best use case."
            ),
        }
        return examples_map.get(a.get("task_type", ""), "")

    @staticmethod
    def _clean(s: str) -> str:
        """Strip trailing punctuation so we can append our own cleanly."""
        return s.strip().rstrip(".!?,;:")

    # Verbs that may survive _core_subject stripping when filler words preceded them
    _RESIDUAL_VERB_RE = re.compile(
        r"^(?:look\s+\w+\s+|analyze\s+|analyse\s+|review\s+|examine\s+|inspect\s+|"
        r"check\s+|assess\s+|evaluate\s+|audit\s+|investigate\s+|explore\s+|research\s+)",
        re.I
    )

    def _clean_subject(self, raw: str, a: dict) -> str:
        """Post-process core_subject: strip residual verbs, trailing vague clauses, normalize entities."""
        subject = a.get("core_subject", raw.strip()[:120])

        # Defense: strip any leading action verb _core_subject missed (e.g. "look throughout"
        # when "please" was stripped first, leaving the verb at the new start of string)
        subject = self._RESIDUAL_VERB_RE.sub("", subject).strip()

        # Strip trailing vague purpose clauses
        subject = re.sub(
            r"\s+and\s+(?:see\s+what\s+to\s+do\s+next|tell\s+me\s+what\s+to\s+do|"
            r"let\s+me\s+know|find\s+out\s+what|figure\s+out\s+what|determine\s+what)"
            r".*$",
            "", subject, flags=re.I,
        ).strip()

        # Normalize common entity names
        subject = re.sub(r"\bgithub\s+commits?\b", "GitHub commit history", subject, flags=re.I)
        subject = re.sub(r"\bgithub\b", "GitHub", subject, flags=re.I)

        # Fallback to raw if result is too short
        if len(subject.strip()) < 8:
            subject = raw.strip()[:80]

        return subject.strip()

    # ── Output format ─────────────────────────────────────────────────

    def _format(self, a: dict, explicit_fmt: str, mode: str = "general", raw: str = "") -> str:
        # Priority 1: always honor explicit user format strictly
        if explicit_fmt:
            key = self._clean(explicit_fmt).lower()
            expanded = _FMT_EXPANSIONS.get(key) or _FMT_EXPANSIONS.get(key.rstrip("s"))
            return expanded if expanded else explicit_fmt

        # Priority 2: multi-task fixed structure
        if a.get("multi_task"):
            domain = a["domains"][0] if a["domains"] else "general"
            section3 = _MULTITASK_SECTION3.get(domain, _MULTITASK_SECTION3["general"])
            return (
                "Return a markdown document with:\n"
                "- Section 1: Summary of the current situation\n"
                "- Section 2: Action plan \u2014 group into: this week / this month / later\n"
                f"- Section 3: {section3}\n"
                "- Section 4: Integrated recommendations and risks"
            )

        task_type = a["task_type"]

        # Priority 3: task-type smart defaults (mode-independent)
        if task_type == "compare":
            return (
                "- A markdown table comparing the options across relevant dimensions\n"
                "- A brief prose summary with a clear recommendation"
            )
        if task_type == "explain":
            return (
                "- Clear prose explanation\n"
                "- At least one practical example or analogy\n"
                "- A summary bullet list of key takeaways"
            )
        if task_type == "fix":
            return (
                "- Root cause explanation in plain language\n"
                "- The fix as a code block (with before/after if applicable)\n"
                "- Bullet points on prevention"
            )
        if task_type == "analyze":
            return (
                "- Findings as a numbered list (most critical first)\n"
                "- Recommendations as a separate numbered list\n"
                "- Summary table: Issue | Severity | Fix"
            )
        if task_type == "list":
            return "Numbered markdown list with a 1–2 sentence explanation for each item."
        if task_type == "write":
            return "Polished, complete prose. Ready to copy-paste as-is."

        # Priority 4: mode-based defaults for build/design and general fallback
        _SEC_RE  = re.compile(r"\b(security|auth|vulnerability|exploit|permission|token|encrypt)\b", re.I)
        _ARCH_RE = re.compile(r"\b(architecture|microservice|design system|distributed|scalable|infra)\b", re.I)

        if mode == "coding" and task_type in ("build", "design"):
            parts = [
                "Provide the response in the following structure:",
                "1. Tech stack summary",
                "2. Step-by-step implementation with code",
                "3. Error handling approach",
                "4. Documentation / usage notes",
            ]
            if _SEC_RE.search(raw):
                parts.append(f"{len(parts)}. Security considerations")
            if _ARCH_RE.search(raw):
                parts.append(f"{len(parts)}. Architecture overview")
            return "\n".join(parts)

        if mode == "general":
            domain = a["domains"][0] if a["domains"] else "general"
            aud_label = "the target audience"
            return (
                "Structure your response as:\n"
                "1. Clear goal restatement\n"
                "2. Main answer / recommendation\n"
                f"3. Key considerations for {aud_label}\n"
                "4. Next steps or action items"
            )

        return "Clear, well-structured prose with headers where appropriate."

    # ── Constraints ───────────────────────────────────────────────────

    def _constraints(self, raw: str, a: dict, tone: str, mode: str = "general") -> str:
        parts = []

        # Preserve explicit constraints from original (sentence-level fact/directive split)
        if a["has_constraints"]:
            raw_sents = [s.strip() for s in _SENT_RE.split(raw) if s.strip()]
            directive_sentences: list[str] = []
            for s in raw_sents:
                is_fact = bool(_FACT_RE.search(s)) and bool(_FACT_NOUN_RE.search(s))
                is_directive = bool(_DIRECTIVE_RE.search(s))
                if is_directive and not is_fact:
                    directive_sentences.append(s[:120])
                elif is_directive and is_fact:
                    # Both: extract only the directive clause.
                    # The 100-char slice is applied BEFORE split(",")[0], so output is ≤ 100 chars
                    # even when no comma is present.
                    m = _DIRECTIVE_RE.search(s)
                    if m:
                        clause = s[m.start():m.start() + 100].split(",")[0].strip()
                        directive_sentences.append(clause)
                if len(directive_sentences) >= 3:
                    break
            for sent in directive_sentences:
                parts.append(f"From original prompt: {sent}")

        # User-supplied tone
        if tone:
            parts.append(f"Tone: {self._clean(tone)}.")

        # Smart defaults by domain
        domain = a["domains"][0] if a["domains"] else "general"
        if domain == "security":
            parts.append("Flag any security risks explicitly. Do not suggest insecure patterns.")
        if domain == "ai_ml":
            parts.append("Be precise about model behavior — distinguish facts from speculation.")
        if a["task_type"] in ("build", "design") and a["is_technical"]:
            parts.append(
                "Show working code, not pseudocode. "
                "If choices depend on the user's stack, offer 2 concrete options."
            )
        if a["task_type"] == "explain" and not a["is_technical"]:
            parts.append("Avoid unexplained jargon. Define technical terms on first use.")

        # Ask for clarification when prompt is vague or ambiguous
        if a["is_short"] or a["task_type"] == "general":
            parts.append("If any requirements are unclear or ambiguous, ask for clarification before proceeding.")

        # Conciseness for non-writing tasks
        if a["task_type"] not in ("write", "list"):
            parts.append("Be direct and concise — avoid filler, repetition, and unnecessary caveats.")

        # Ensure at least 2 strong constraint bullets
        if not parts:
            parts.extend(_STRONGER_DEFAULTS)
        elif len(parts) < 2:
            for default in _STRONGER_DEFAULTS:
                if len(parts) >= 2:
                    break
                if default not in parts:
                    parts.append(default)

        return "\n".join(f"- {p}" for p in parts)

# ---------------------------------------------------------------------------
# GuideMeDialog
# ---------------------------------------------------------------------------

class GuideMeDialog(tk.Toplevel):
    QUESTIONS = [
        ("model",      "Which AI tool will you use this with?",   "e.g. Claude, GPT-4"),
        ("audience",   "Who is the target audience?",              "e.g. junior developer, non-technical user"),
        ("output_fmt", "What format should the output be in?",     "e.g. bullet points, JSON, markdown table"),
        ("tone",       "Any tone or style constraints?",           "e.g. concise, step-by-step, max 200 words"),
        ("mode",       "What mode should the output use?",         "e.g. coding, general"),
    ]

    def __init__(self, parent, on_complete):
        super().__init__(parent)
        self.title("Guide Me")
        self.configure(bg=C["surface"])
        self.resizable(False, False)
        self.grab_set()
        self.on_complete = on_complete
        self.answers = {}
        self._step = 0
        self._var = tk.StringVar()
        self._build()
        self._go()
        self._center(parent)

    def _build(self):
        pad = tk.Frame(self, bg=C["surface"], padx=32, pady=28)
        pad.pack(fill=tk.BOTH, expand=True)

        # Step indicator + progress bar
        top = tk.Frame(pad, bg=C["surface"])
        top.pack(fill=tk.X, pady=(0, 16))
        self._step_lbl = tk.Label(top, text="", font=F["xs"],
                                  bg=C["surface"], fg=C["text2"], anchor="w")
        self._step_lbl.pack(side=tk.LEFT)

        self._prog = tk.Canvas(pad, height=3, bg=C["border"],
                               highlightthickness=0, bd=0)
        self._prog.pack(fill=tk.X, pady=(0, 20))

        self._q_lbl = tk.Label(pad, text="", font=F["ui_b"],
                               bg=C["surface"], fg=C["text"],
                               wraplength=360, justify="left", anchor="w")
        self._q_lbl.pack(fill=tk.X, pady=(0, 4))

        self._hint_lbl = tk.Label(pad, text="", font=F["xs"],
                                  bg=C["surface"], fg=C["muted"], anchor="w")
        self._hint_lbl.pack(fill=tk.X, pady=(0, 12))

        self._entry = tk.Entry(
            pad, textvariable=self._var, font=F["ui"], width=40,
            relief=tk.FLAT, bd=0, highlightthickness=1,
            highlightbackground=C["border"], highlightcolor=C["accent"],
            bg=C["surface2"], fg=C["text"],
            insertbackground=C["accent"],
            selectbackground=C["accent"], selectforeground="#ffffff",
        )
        self._entry.pack(fill=tk.X, ipady=8, pady=(0, 24))
        self._entry.bind("<Return>", lambda _: self._next())

        btns = tk.Frame(pad, bg=C["surface"])
        btns.pack(fill=tk.X)

        self._skip = tk.Button(btns, text="Skip", font=F["sm"],
                               command=self._skip_step,
                               relief=tk.FLAT, bd=0, cursor="hand2",
                               bg=C["surface"], fg=C["text2"],
                               activebackground=C["surface2"],
                               activeforeground=C["text"],
                               padx=12, pady=6)
        self._skip.pack(side=tk.LEFT)
        self._skip.bind("<Enter>", lambda e: self._skip.config(fg=C["text"]))
        self._skip.bind("<Leave>", lambda e: self._skip.config(fg=C["text2"]))

        self._nxt = tk.Button(btns, text="Next →", font=F["ui_b"],
                              command=self._next,
                              relief=tk.FLAT, bd=0, cursor="hand2",
                              bg=C["btn_p"], fg=C["btn_p_fg"],
                              activebackground=C["accent"],
                              activeforeground="#ffffff",
                              padx=20, pady=6)
        self._nxt.pack(side=tk.RIGHT)
        self._nxt.bind("<Enter>", lambda e: self._nxt.config(bg=C["btn_p_hov"]))
        self._nxt.bind("<Leave>", lambda e: self._nxt.config(bg=C["btn_p"]))

    def _go(self):
        total = len(self.QUESTIONS)
        _, q, hint = self.QUESTIONS[self._step]
        self._step_lbl.config(text=f"Step {self._step+1} of {total}")
        self._q_lbl.config(text=q)
        self._hint_lbl.config(text=hint)
        self._var.set("")
        self._entry.focus_set()
        self._nxt.config(text="Finish ✓" if self._step == total-1 else "Next →")
        # Progress bar
        self._prog.update_idletasks()
        w = self._prog.winfo_width()
        if w > 1:
            self._prog.delete("all")
            filled = int(w * (self._step+1) / total)
            self._prog.create_rectangle(0, 0, filled, 3,
                                        fill=C["accent"], outline="")

    def _next(self):
        self.answers[self.QUESTIONS[self._step][0]] = self._var.get().strip()
        self._advance()

    def _skip_step(self):
        self.answers[self.QUESTIONS[self._step][0]] = ""
        self._advance()

    def _advance(self):
        self._step += 1
        if self._step >= len(self.QUESTIONS):
            self.destroy()
            self.on_complete(self.answers)
        else:
            self._go()

    def _center(self, parent):
        self.update_idletasks()
        x = parent.winfo_rootx() + parent.winfo_width()//2 - self.winfo_width()//2
        y = parent.winfo_rooty() + parent.winfo_height()//2 - self.winfo_height()//2
        self.geometry(f"+{x}+{y}")

# ---------------------------------------------------------------------------
# PromptImproverApp
# ---------------------------------------------------------------------------

_FIELDS = [
    ("model",      "Model",    "Claude, GPT-4…"),
    ("audience",   "Audience", "junior dev, non-technical…"),
    ("output_fmt", "Format",   "bullets, JSON, table…"),
    ("tone",       "Tone",     "concise, step-by-step…"),
    ("mode",       "Mode",     "coding, general…"),
]

_ELEMENTS = [
    ("has_role",          "Role"),
    ("has_context",       "Context"),
    ("has_task",          "Task"),
    ("has_output_format", "Format"),
    ("has_constraints",   "Constraints"),
    ("mode",              "Mode"),
]


class PromptImproverApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(WINDOW_TITLE)
        self.root.minsize(MIN_WIDTH, MIN_HEIGHT)
        self.root.configure(bg=C["bg"])
        self._improved_text = ""
        self._entries: dict[str, tk.Entry] = {}
        self._ph_active: dict[str, bool] = {}
        self._badge_frames: dict[str, tk.Frame] = {}
        self._badge_labels: dict[str, tk.Label] = {}

        self._build()
        self._center()
        self.root.bind("<Control-Return>", lambda _: self._improve())
        self.root.bind("<Command-Return>",  lambda _: self._improve())

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _build(self):
        paned = tk.PanedWindow(
            self.root, orient=tk.HORIZONTAL,
            bg=C["border"], sashwidth=1, sashrelief=tk.FLAT, handlesize=0,
        )
        paned.pack(fill=tk.BOTH, expand=True)

        left  = tk.Frame(paned, bg=C["panel_l"])
        right = tk.Frame(paned, bg=C["panel_r"])
        paned.add(left,  minsize=360, stretch="always")
        paned.add(right, minsize=440, stretch="always")

        self._build_left(left)
        self._build_right(right)
        self.root.after(60, lambda: paned.sash_place(0, 420, 0))

    # ── LEFT PANE ──────────────────────────────────────────────────────

    def _build_left(self, p: tk.Frame):
        # Header bar
        hdr = tk.Frame(p, bg=C["surface"], height=44)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)
        tk.Label(hdr, text="✦  Prompt Improver", font=F["title"],
                 bg=C["surface"], fg=C["text"], padx=16).pack(side=tk.LEFT, fill=tk.Y)
        tk.Frame(p, bg=C["border"], height=1).pack(fill=tk.X)

        # ── Raw prompt area ────────────────────────────────────────────
        prompt_lbl_row = tk.Frame(p, bg=C["panel_l"])
        prompt_lbl_row.pack(fill=tk.X, padx=16, pady=(12, 4))
        tk.Label(prompt_lbl_row, text="YOUR PROMPT", font=F["xs"],
                 bg=C["panel_l"], fg=C["text2"]).pack(side=tk.LEFT)
        tk.Frame(prompt_lbl_row, bg=C["border"], height=1).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(8,0))

        text_wrap = tk.Frame(p, bg=C["border"], padx=1, pady=1)
        text_wrap.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 12))

        self._input_text = tk.Text(
            text_wrap, font=F["mono"], wrap=tk.WORD,
            relief=tk.FLAT, bd=0, highlightthickness=0,
            bg=C["surface2"], fg=C["text"],
            insertbackground=C["accent"],
            selectbackground=C["accent"], selectforeground="#ffffff",
            undo=True, spacing1=3, spacing3=3, padx=12, pady=10,
        )
        self._bind_scroll(self._input_text)

        # Minimal scrollbar — only show on non-mac or if content overflows
        if _SYSTEM != "Darwin":
            sb = self._make_sb(text_wrap, self._input_text.yview)
            self._input_text.configure(yscrollcommand=sb.set)
            sb.pack(side=tk.RIGHT, fill=tk.Y)
        self._input_text.pack(fill=tk.BOTH, expand=True)

        # ── Options (compact 2×2 grid) ─────────────────────────────────
        opts_lbl_row = tk.Frame(p, bg=C["panel_l"])
        opts_lbl_row.pack(fill=tk.X, padx=16, pady=(0, 4))
        tk.Label(opts_lbl_row, text="OPTIONS", font=F["xs"],
                 bg=C["panel_l"], fg=C["text2"]).pack(side=tk.LEFT)
        tk.Frame(opts_lbl_row, bg=C["border"], height=1).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(8,0))

        opts = tk.Frame(p, bg=C["surface"], padx=14, pady=10)
        opts.pack(fill=tk.X, padx=16, pady=(0, 12))

        n = len(_FIELDS)
        for col, (key, label, ph) in enumerate(_FIELDS):
            is_last_lone = (col == n - 1) and (n % 2 == 1)
            cell = tk.Frame(opts, bg=C["surface"])
            cell.grid(row=col//2, column=col%2,
                      columnspan=2 if is_last_lone else 1,
                      sticky="ew",
                      padx=(0 if col%2==0 else 6, 6 if col%2==0 else 0),
                      pady=4)
            tk.Label(cell, text=label, font=F["xs"],
                     bg=C["surface"], fg=C["text2"],
                     anchor="w").pack(fill=tk.X)
            e = tk.Entry(
                cell, font=F["sm"], relief=tk.FLAT, bd=0,
                highlightthickness=1,
                highlightbackground=C["border"],
                highlightcolor=C["accent"],
                bg=C["surface2"], fg=C["muted"],
                insertbackground=C["accent"],
                selectbackground=C["accent"], selectforeground="#ffffff",
            )
            e.pack(fill=tk.X, ipady=5)
            opts.columnconfigure(col%2, weight=1)
            self._entries[key] = e
            self._ph_active[key] = False
            self._install_ph(e, key, ph)

        # ── Action buttons ─────────────────────────────────────────────
        tk.Frame(p, bg=C["border"], height=1).pack(fill=tk.X)
        btn_bar = tk.Frame(p, bg=C["panel_l"], padx=16, pady=12)
        btn_bar.pack(fill=tk.X)

        self._btn_guide = self._btn(btn_bar, "Guide Me", self._guide, "sec")
        self._btn_guide.pack(side=tk.LEFT, padx=(0, 8))

        self._btn_improve = self._btn(btn_bar, "Improve  ⌘↵", self._improve, "pri")
        self._btn_improve.pack(side=tk.LEFT)

        hint = "Ctrl+Enter" if _SYSTEM != "Darwin" else "Cmd+Return"
        tk.Label(btn_bar, text=f"  or {hint}", font=F["xs"],
                 bg=C["panel_l"], fg=C["muted"]).pack(side=tk.LEFT)

    # ── RIGHT PANE ─────────────────────────────────────────────────────

    def _build_right(self, p: tk.Frame):
        # Header bar
        hdr = tk.Frame(p, bg=C["surface"], height=44)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)
        tk.Label(hdr, text="Improved Prompt", font=F["title"],
                 bg=C["surface"], fg=C["text"], padx=16).pack(side=tk.LEFT, fill=tk.Y)

        self._copy_btn = self._btn(hdr, "Copy", self._copy, "sec")
        self._copy_btn.pack(side=tk.RIGHT, padx=12, pady=8)
        tk.Frame(p, bg=C["border"], height=1).pack(fill=tk.X)

        # Output text area
        text_wrap = tk.Frame(p, bg=C["panel_r"])
        text_wrap.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        self._output_text = tk.Text(
            text_wrap, font=F["mono"], wrap=tk.WORD,
            relief=tk.FLAT, bd=0, highlightthickness=0,
            bg=C["panel_r"], fg=C["text"],
            selectbackground=C["accent"], selectforeground="#ffffff",
            state=tk.DISABLED,
            spacing1=3, spacing3=3, padx=20, pady=14,
        )
        # Tags for styled output rendering
        self._output_text.tag_configure(
            "section_hdr",
            foreground=C["accent"],
            font=F["ui_b"],
            spacing1=8,   # extra space above section headers
        )
        self._output_text.tag_configure(
            "divider",
            foreground=C["text2"],
        )
        self._bind_scroll(self._output_text)

        if _SYSTEM != "Darwin":
            sb = self._make_sb(text_wrap, self._output_text.yview)
            self._output_text.configure(yscrollcommand=sb.set)
            sb.pack(side=tk.RIGHT, fill=tk.Y)
        self._output_text.pack(fill=tk.BOTH, expand=True)

        # ── Analysis strip ─────────────────────────────────────────────
        tk.Frame(p, bg=C["border"], height=1).pack(fill=tk.X)
        analysis_bar = tk.Frame(p, bg=C["surface"], padx=16, pady=10)
        analysis_bar.pack(fill=tk.X)

        lbl_row = tk.Frame(analysis_bar, bg=C["surface"])
        lbl_row.pack(fill=tk.X, pady=(0, 8))
        tk.Label(lbl_row, text="ANALYSIS", font=F["xs"],
                 bg=C["surface"], fg=C["text2"]).pack(side=tk.LEFT)

        badges_row = tk.Frame(analysis_bar, bg=C["surface"])
        badges_row.pack(fill=tk.X)
        for key, label in _ELEMENTS:
            outer, lbl = self._badge(badges_row, f"○  {label}", "neutral")
            outer.pack(side=tk.LEFT, padx=(0, 6), pady=2)
            self._badge_frames[key] = outer
            self._badge_labels[key] = lbl

        self._notice_lbl = tk.Label(
            analysis_bar, text="", font=F["xs"],
            bg=C["surface"], fg=C["warn"], anchor="w",
        )
        self._notice_lbl.pack(fill=tk.X, pady=(6, 0))

    # ------------------------------------------------------------------
    # Helpers: scrollbar, button, placeholder, badge
    # ------------------------------------------------------------------

    def _make_sb(self, parent, cmd):
        return tk.Scrollbar(
            parent, command=cmd, orient=tk.VERTICAL,
            bg=C["scroll"], troughcolor=C["scroll"],
            activebackground=C["scroll_hov"],
            relief=tk.FLAT, bd=0, width=6,
        )

    @staticmethod
    def _bind_scroll(widget):
        """Enable trackpad / mousewheel scrolling without a scrollbar widget."""
        def _scroll(event):
            # macOS trackpad sends delta in units of 120
            delta = -1 * (event.delta // 120) if _SYSTEM == "Darwin" else \
                    -1 * (event.delta // 120)
            widget.yview_scroll(delta, "units")
        widget.bind("<MouseWheel>", _scroll)
        widget.bind("<Button-4>",  lambda e: widget.yview_scroll(-1, "units"))
        widget.bind("<Button-5>",  lambda e: widget.yview_scroll( 1, "units"))

    def _btn(self, parent, text, cmd, style="pri", **kw):
        if style == "pri":
            bg, fg, hov = C["btn_p"], C["btn_p_fg"], C["btn_p_hov"]
            font = F["ui_b"]
        else:
            bg, fg, hov = C["btn_s"], C["btn_s_fg"], C["btn_s_hov"]
            font = F["ui"]
        b = tk.Button(parent, text=text, command=cmd,
                      relief=tk.FLAT, bd=0, cursor="hand2",
                      bg=bg, fg=fg, activebackground=hov, activeforeground=fg,
                      font=font, padx=14, pady=6, **kw)
        b.bind("<Enter>", lambda e: b.config(bg=hov))
        b.bind("<Leave>", lambda e: b.config(bg=bg))
        return b

    def _install_ph(self, e: tk.Entry, key: str, text: str):
        def show():
            e.delete(0, tk.END)
            e.insert(0, text)
            e.config(fg=C["muted"])
            self._ph_active[key] = True

        def on_in(ev=None):
            if self._ph_active[key]:
                e.delete(0, tk.END)
                e.config(fg=C["text"])
                self._ph_active[key] = False

        def on_out(ev=None):
            if e.get().strip() == "":
                show()

        e.bind("<FocusIn>",  on_in)
        e.bind("<FocusOut>", on_out)
        show()

    def _get(self, key: str) -> str:
        return "" if self._ph_active.get(key) else self._entries[key].get().strip()

    @staticmethod
    def _badge(parent, text, state):
        colors = {
            "ok":      (C["ok_dim"],   C["ok"]),
            "warn":    (C["warn_dim"], C["warn"]),
            "neutral": (C["surface2"], C["text2"]),
        }
        bg, fg = colors[state]
        outer = tk.Frame(parent, bg=bg)
        lbl = tk.Label(outer, text=text, font=F["mono_sm"],
                       bg=bg, fg=fg, padx=8, pady=3, anchor="w")
        lbl.pack()
        return outer, lbl

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _improve(self):
        raw = self._input_text.get("1.0", tk.END).strip()
        if not raw:
            messagebox.showwarning(
                "Empty prompt",
                "Type or paste a prompt on the left before clicking Improve.",
                parent=self.root,
            )
            return

        analysis = PromptAnalyzer().analyze(raw)
        meta     = {k: self._get(k) for k in self._entries}
        # Inject inferred mode for badge display
        mode_override = meta.get("mode", "").strip().lower()
        analysis["_inferred_mode"] = (
            mode_override if mode_override in ("coding", "general")
            else ("coding" if analysis.get("is_technical") else "general")
        )
        result   = PromptBuilder().build(raw, analysis, meta)
        self._improved_text = result

        self._output_text.config(state=tk.NORMAL)
        self._output_text.delete("1.0", tk.END)
        self._output_text.insert("1.0", result)

        # Style [SECTION] headers and <xml> tags in accent color, "---" dividers in muted
        for i, line in enumerate(result.split("\n"), start=1):
            stripped = line.strip()
            if (stripped.startswith("[") and stripped.endswith("]")) or \
               (stripped.startswith("<") and not stripped.startswith("</")):
                self._output_text.tag_add("section_hdr", f"{i}.0", f"{i}.end")
            elif stripped.startswith("</"):
                self._output_text.tag_add("section_hdr", f"{i}.0", f"{i}.end")
            elif stripped == "---":
                self._output_text.tag_add("divider", f"{i}.0", f"{i}.end")

        self._output_text.config(state=tk.DISABLED)

        self._update_badges(analysis)

    def _copy(self):
        if not self._improved_text:
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(self._improved_text)
        self._copy_btn.config(text="Copied ✓", fg=C["ok"], bg=C["btn_s"])
        self.root.after(1500, lambda: self._copy_btn.config(
            text="Copy", fg=C["btn_s_fg"], bg=C["btn_s"],
        ))

    def _guide(self):
        def done(answers):
            for k, v in answers.items():
                if k in self._entries and v:
                    self._entries[k].delete(0, tk.END)
                    self._entries[k].insert(0, v)
                    self._entries[k].config(fg=C["text"])
                    self._ph_active[k] = False
            self._improve()
        GuideMeDialog(self.root, done)

    def _update_badges(self, a: dict):
        for key, label in _ELEMENTS:
            if key == "mode":
                mode_val = a.get("_inferred_mode", "general")
                is_coding = (mode_val == "coding")
                text = f"◈  {label}: {'Coding' if is_coding else 'General'}"
                bg = C["ok_dim"]  if is_coding else C["surface2"]
                fg = C["accent"]  if is_coding else C["text2"]
                self._badge_frames[key].config(bg=bg)
                self._badge_labels[key].config(text=text, bg=bg, fg=fg)
            else:
                present = a.get(key, False)
                sym = "✓" if present else "✗"
                suf = "" if present else "  added"
                bg = C["ok_dim"]   if present else C["warn_dim"]
                fg = C["ok"]       if present else C["warn"]
                self._badge_frames[key].config(bg=bg)
                self._badge_labels[key].config(text=f"{sym}  {label}{suf}", bg=bg, fg=fg)

        notices = []
        if a.get("is_short"):
            notices.append("⚠  Very brief — try adding more detail.")
        if a.get("is_long"):
            notices.append("⚠  Very long — elements truncated.")
        self._notice_lbl.config(text="   ".join(notices))

    # ------------------------------------------------------------------
    def _center(self):
        self.root.update_idletasks()
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        x = (sw - INITIAL_WIDTH)  // 2
        y = (sh - INITIAL_HEIGHT) // 2
        self.root.geometry(f"{INITIAL_WIDTH}x{INITIAL_HEIGHT}+{x}+{y}")

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    root = tk.Tk()
    PromptImproverApp(root)
    root.mainloop()
