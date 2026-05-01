from __future__ import annotations


EXECUTION_RISK_RULES = (
    {
        "label": "curl-pipe-shell",
        "severity": 2.0,
        "patterns": (
            r"curl\b[^\n|]{0,300}\|\s*(?:bash|sh)\b",
            r"wget\b[^\n|]{0,300}\|\s*(?:bash|sh)\b",
        ),
    },
    {
        "label": "dynamic-exec",
        "severity": 2.0,
        "patterns": (
            r"\binvoke-expression\b",
            r"\biex\b",
            r"\beval\s*\(",
            r"\bexec\s*\(",
        ),
    },
    {
        "label": "persistence-hook",
        "severity": 2.0,
        "patterns": (
            r"\bcrontab\b",
            r"\bsystemctl\b",
            r"\bschtasks\b",
            r"\blaunchctl\b",
        ),
    },
    {
        "label": "shell-exec",
        "severity": 1.0,
        "patterns": (
            r"subprocess\.(?:run|popen)\s*\(",
            r"os\.system\s*\(",
            r"shell\s*=\s*true",
            r"child_process\.(?:exec|spawn)\s*\(",
        ),
    },
)
