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
    # finance (placed before business so finance-specific signals win ties over generic business signals)
    ("finances",        "finance"), ("budget",         "finance"), ("spending",      "finance"),
    ("income",          "finance"), ("expenses",       "finance"), ("cash flow",     "finance"),
    ("credit card",     "finance"), ("amex",           "finance"), ("visa card",     "finance"),
    ("mastercard",      "finance"), (" apr ",          "finance"), ("points",        "finance"),
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
_ANALYZE_RE  = re.compile(r"\b(analyze|analyse|review|audit|evaluate|assess|critique|improve my|optimize)\b", re.I)
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
    r'^\s*(please\s+)?(what|how|why|when|can you|could you|help me|i need|i want|'
    r'tell me|look at|review|summarize|list|analyze|build|plan|check|explain|find|'
    r'show|give|create|make|write|compare|evaluate|assess)\b',
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
        # Strip leading imperative verb
        cleaned = re.sub(
            r"^(make|build|create|design|write|explain|compare|fix|debug|"
            r"analyze|analyse|help me|can you|please|i want to|i need to)\s+",
            "", text.strip(), flags=re.I,
        )
        # Take up to first sentence or 120 chars
        first = _SENT_RE.split(cleaned)[0].strip()
        return first[:120]

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
}


class PromptBuilder:

    def build(self, raw: str, analysis: dict, meta: dict) -> str:
        model  = meta.get("model",      "").strip()
        aud    = meta.get("audience",   "").strip()
        fmt    = meta.get("output_fmt", "").strip()
        tone   = meta.get("tone",       "").strip()

        secs = []
        secs.append(f"[ROLE / PERSONA]\n{self._role(analysis, model)}")
        secs.append(f"[CONTEXT]\n{self._context(raw, analysis, aud)}")
        secs.append(f"[TASK]\n{self._task(raw, analysis)}")

        inp = self._input_desc(raw, analysis)
        if inp:
            secs.append(f"[INPUT]\n{inp}")

        secs.append(f"[OUTPUT FORMAT]\n{self._format(analysis, fmt)}")
        secs.append(f"[CONSTRAINTS & STYLE]\n{self._constraints(raw, analysis, tone)}")

        body = "\n\n".join(secs)
        if analysis.get("is_long"):
            body += "\n\n⚠ Original prompt was very long; some elements were truncated."
        return body + f"\n\n{USAGE_NOTE}"

    # ── Role ──────────────────────────────────────────────────────────

    def _role(self, a: dict, model: str) -> str:
        if a["has_role"]:
            return "(role already specified in your prompt — preserved as-is)"

        primary_domain = a["domains"][0] if a["domains"] else "general"
        role_desc, _ = _DOMAIN_ROLES.get(primary_domain, _DOMAIN_ROLES["general"])

        # Enrich with specific tech stack if available
        tech = a.get("tech_stack", [])
        if tech and primary_domain not in ("education", "writing", "business", "general"):
            tech_str = ", ".join(tech[:3])
            role_desc = role_desc.rstrip(".") + f", with hands-on experience in {tech_str}"

        suffix = f", optimized for use with {model}" if model else ""
        return f"You are {role_desc}{suffix}."

    # ── Context ───────────────────────────────────────────────────────

    def _context(self, raw: str, a: dict, aud: str) -> str:
        lines = []

        # 1. Summarize what the user is actually trying to do
        subject  = a.get("core_subject", raw.strip()[:100])
        task_type = a["task_type"]
        verb_map = {
            "build":   "build", "design": "design", "explain": "understand",
            "compare": "compare", "fix": "fix a problem with",
            "analyze": "analyze", "write": "write", "list": "find",
            "general": "work on",
        }
        verb = verb_map.get(task_type, "work on")
        lines.append(f"The goal is to {verb}: {subject}.")

        # 2. Inject domain knowledge for technical domains
        domain_context = {
            "backend":  "This is a backend engineering task involving server-side code, APIs, or infrastructure.",
            "devops":   "This is a DevOps/infrastructure task involving deployment, cloud services, or automation.",
            "frontend": "This is a frontend development task involving UI components, browser rendering, or user experience.",
            "ai_ml":    "This is an AI/ML task involving language models, model behavior, or intelligent system design.",
            "security": "This is a security task — prioritize safety, avoid harmful patterns, and flag potential risks.",
            "data":     "This is a data engineering or analytics task involving data processing, modeling, or visualization.",
            "mobile":   "This is a mobile development task targeting iOS, Android, or cross-platform environments.",
        }
        domain = a["domains"][0] if a["domains"] else "general"
        if domain in domain_context:
            lines.append(domain_context[domain])

        # 3. Call out specific technologies so the AI focuses on them
        tech = a.get("tech_stack", [])
        if tech:
            lines.append(f"Key technologies involved: {', '.join(tech[:5])}.")

        # 4. Audience
        if aud:
            lines.append(f"Target audience: {aud}.")
        elif a["is_technical"]:
            lines.append("Assume a technical developer audience familiar with the relevant concepts.")
        else:
            lines.append("Assume a general audience — avoid unnecessary jargon.")

        return "\n".join(lines)

    # ── Task ──────────────────────────────────────────────────────────

    def _task(self, raw: str, a: dict) -> str:
        subject   = a.get("core_subject", raw.strip()[:120])
        task_type = a["task_type"]
        tech      = a.get("tech_stack", [])
        tech_str  = f" using {', '.join(tech[:2])}" if tech else ""

        expansions = {
            "build": (
                f"Design and implement {subject}{tech_str}.\n"
                f"Cover: (1) overall architecture and how components fit together, "
                f"(2) step-by-step implementation with concrete code examples, "
                f"(3) any configuration, auth, or security considerations."
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
                f"Cover: (1) current state and what's working, "
                f"(2) issues, gaps, or risks identified, "
                f"(3) specific actionable recommendations, "
                f"(4) priority order for improvements."
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
            return expansions[task_type]

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

    @staticmethod
    def _clean(s: str) -> str:
        """Strip trailing punctuation so we can append our own cleanly."""
        return s.strip().rstrip(".!?,;:")

    # ── Output format ─────────────────────────────────────────────────

    def _format(self, a: dict, explicit_fmt: str) -> str:
        if explicit_fmt:
            key = self._clean(explicit_fmt).lower()
            expanded = _FMT_EXPANSIONS.get(key) or _FMT_EXPANSIONS.get(key.rstrip("s"))
            return expanded if expanded else explicit_fmt

        task_type = a["task_type"]
        domain    = a["domains"][0] if a["domains"] else "general"

        # Task-type-driven smart defaults
        if task_type in ("build", "design") and a["is_technical"]:
            return (
                "- Section 1: High-level architecture (1–2 paragraphs)\n"
                "- Section 2: Key components or tools in a markdown table "
                "(columns: Name | Purpose | Notes)\n"
                "- Section 3: Step-by-step implementation with code snippets\n"
                "- Section 4: Security, edge cases, and gotchas as bullet points"
            )
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

        return "Clear, well-structured prose with headers where appropriate."

    # ── Constraints ───────────────────────────────────────────────────

    def _constraints(self, raw: str, a: dict, tone: str) -> str:
        parts = []

        # Preserve explicit constraints from original
        if a["has_constraints"]:
            m = _CON_PAT.search(raw)
            if m:
                snippet = raw[m.start():m.start()+150].split("\n")[0].strip()
                parts.append(f"From original prompt: {snippet}")

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

        # Fallback
        if not parts:
            parts.append("Be specific and actionable. Avoid vague generalities.")

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
]

_ELEMENTS = [
    ("has_role",          "Role"),
    ("has_context",       "Context"),
    ("has_task",          "Task"),
    ("has_output_format", "Format"),
    ("has_constraints",   "Constraints"),
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

        for col, (key, label, ph) in enumerate(_FIELDS):
            cell = tk.Frame(opts, bg=C["surface"])
            cell.grid(row=col//2, column=col%2, sticky="ew",
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
        result   = PromptBuilder().build(raw, analysis, meta)
        self._improved_text = result

        self._output_text.config(state=tk.NORMAL)
        self._output_text.delete("1.0", tk.END)
        self._output_text.insert("1.0", result)

        # Style [SECTION] headers in accent color and "---" dividers in muted
        for i, line in enumerate(result.split("\n"), start=1):
            stripped = line.strip()
            if stripped.startswith("[") and stripped.endswith("]"):
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
