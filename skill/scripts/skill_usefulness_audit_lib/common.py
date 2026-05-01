from __future__ import annotations

from .constants import *

def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def normalize_name(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-{2,}", "-", value)
    return value.strip("-")


def normalize_pathish(value) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    resolved = Path(text).expanduser().resolve()
    normalized = os.path.normcase(os.path.normpath(str(resolved)))
    return normalized.replace("\\", "/")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def is_cjk_char(char: str) -> bool:
    code = ord(char)
    return (
        0x3400 <= code <= 0x4DBF
        or 0x4E00 <= code <= 0x9FFF
        or 0xF900 <= code <= 0xFAFF
        or 0x20000 <= code <= 0x2A6DF
        or 0x2A700 <= code <= 0x2B73F
        or 0x2B740 <= code <= 0x2B81F
        or 0x2B820 <= code <= 0x2CEAF
    )


def estimate_context_units(text: str) -> int:
    if not text:
        return 0
    ascii_chars = 0
    cjk_chars = 0
    other_chars = 0
    for char in text:
        if ord(char) < 128:
            ascii_chars += 1
        elif is_cjk_char(char):
            cjk_chars += 1
        else:
            other_chars += 1
    return math.ceil(
        ascii_chars / TEXT_BYTES_PER_CONTEXT_UNIT
        + cjk_chars * CJK_CONTEXT_UNITS_PER_CHAR
        + other_chars * NON_ASCII_CONTEXT_UNITS_PER_CHAR
    )


def file_size(path: Path) -> int:
    try:
        return path.stat().st_size
    except OSError:
        return 0


def sorted_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted((item for item in root.rglob("*") if item.is_file()), key=lambda item: item.as_posix())


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Parse flat scalar frontmatter fields used by this skill bundle."""
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    raw_yaml = parts[1]
    body = parts[2].lstrip("\r\n")
    data: dict[str, str] = {}
    for line in raw_yaml.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip('"').strip("'")
    return data, body


def extract_terms(text: str) -> set[str]:
    raw_terms = re.findall(r"[a-z0-9][a-z0-9+.]*|[\u4e00-\u9fff]{1,}", text.lower().replace("-", " "))
    terms = set()
    for term in raw_terms:
        if term in STOPWORDS:
            continue
        if term.isascii() and len(term) == 1:
            continue
        terms.add(term)
    return terms


def jaccard(left: set[str], right: set[str]) -> float:
    if not left and not right:
        return 0.0
    union = left | right
    if not union:
        return 0.0
    return len(left & right) / len(union)


def guess_source(path: Path) -> str:
    joined = "/".join(part.lower() for part in path.parts)
    if "/.system/" in joined:
        return "system"
    if "/plugins/cache/" in joined:
        return "plugin"
    if "/skills/" in joined:
        return "user"
    return "other"


def guess_namespace(path: Path) -> str:
    lowered = [part.lower() for part in path.parts]
    if "plugins" in lowered and "cache" in lowered:
        cache_index = lowered.index("cache")
        if cache_index + 2 < len(path.parts):
            return normalize_name(path.parts[cache_index + 2])
    source = guess_source(path)
    if source in {"system", "user"}:
        return source
    return "other"


def parse_dateish(value) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        stamp = float(value)
        if stamp > 1_000_000_000_000:
            stamp = stamp / 1000.0
        try:
            return datetime.fromtimestamp(stamp, tz=timezone.utc).date()
        except (OverflowError, OSError, ValueError):
            return None
    if not isinstance(value, str):
        return None

    text = value.strip()
    if not text:
        return None

    normalized = text.replace("Z", "+00:00").replace("z", "+00:00")
    try:
        return datetime.fromisoformat(normalized).date()
    except ValueError:
        pass

    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def normalize_dateish(value) -> str | None:
    parsed = parse_dateish(value)
    if parsed is None:
        return None
    return parsed.isoformat()


def days_since(value) -> int | None:
    parsed = parse_dateish(value)
    if parsed is None:
        return None
    return (date.today() - parsed).days


def load_json_or_jsonl(path: Path):
    text = read_text(path)
    if path.suffix.lower() == ".jsonl":
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    return json.loads(text)


def coerce_int(value) -> int | None:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(float(value))
        except ValueError:
            return None
    return None


def coerce_float(value) -> float | None:
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def current_script_relative_to(root: Path) -> Path | None:
    try:
        return Path(__file__).resolve().relative_to(root.resolve())
    except ValueError:
        return None


def coerce_bool(value) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "yes", "1", "pass", "passed", "success", "succeeded", "ok", "成功", "通过"}:
            return True
        if lowered in {"false", "no", "0", "fail", "failed", "error", "errored", "失败", "未通过"}:
            return False
    return None


def lowered_mapping(mapping: dict) -> dict[str, object]:
    return {str(key).lower(): value for key, value in mapping.items()}


def first_present(
    mapping: dict,
    keys: tuple[str, ...] | list[str],
    lowered: dict[str, object] | None = None,
) -> object | None:
    if lowered is None:
        lowered = lowered_mapping(mapping)
    for key in keys:
        if key in mapping:
            return mapping[key]
        if key.lower() in lowered:
            return lowered[key.lower()]
    return None


def extract_record_identity(mapping: dict, hint_name: str | None = None) -> dict[str, str]:
    lowered = lowered_mapping(mapping)
    explicit_name = normalize_name(str(first_present(mapping, NAME_KEYS, lowered) or ""))
    slug = normalize_name(str(first_present(mapping, SLUG_KEYS, lowered) or ""))
    identifier = normalize_name(str(first_present(mapping, IDENTIFIER_KEYS, lowered) or ""))
    source = normalize_name(str(first_present(mapping, SOURCE_KEYS, lowered) or ""))
    namespace = normalize_name(str(first_present(mapping, NAMESPACE_KEYS, lowered) or ""))
    path = normalize_pathish(first_present(mapping, PATH_KEYS, lowered)) or ""
    name = explicit_name or slug or identifier or normalize_name(str(hint_name or ""))
    return {
        "name": name,
        "slug": slug,
        "identifier": identifier,
        "source": source,
        "namespace": namespace,
        "path": path,
    }


def record_lookup_key(identity: dict[str, str]) -> str | None:
    if identity["path"]:
        return f"path:{identity['path']}"
    if identity["namespace"] and identity["slug"]:
        return f"namespace:{identity['namespace']}:{identity['slug']}"
    if identity["namespace"] and identity["name"]:
        return f"namespace:{identity['namespace']}:{identity['name']}"
    if identity["source"] and identity["slug"]:
        return f"source:{identity['source']}:{identity['slug']}"
    if identity["source"] and identity["name"]:
        return f"source:{identity['source']}:{identity['name']}"
    if identity["slug"]:
        return f"slug:{identity['slug']}"
    if identity["identifier"]:
        return f"id:{identity['identifier']}"
    if identity["name"]:
        return f"name:{identity['name']}"
    return None


def skill_lookup_keys(skill: dict[str, object]) -> list[str]:
    keys = [f"path:{normalize_pathish(skill['path'])}"]
    namespace = str(skill.get("namespace") or "")
    source = str(skill.get("source") or "")
    slug = str(skill.get("slug") or "")
    name = str(skill.get("name") or "")
    if namespace and slug:
        keys.append(f"namespace:{namespace}:{slug}")
    if namespace and name:
        keys.append(f"namespace:{namespace}:{name}")
    if source and slug:
        keys.append(f"source:{source}:{slug}")
    if source and name:
        keys.append(f"source:{source}:{name}")
    if slug:
        keys.append(f"slug:{slug}")
    if name:
        keys.append(f"name:{name}")
    return [key for key in keys if key]


def resolve_record(
    store: dict[str, dict[str, object]],
    skill: dict[str, object],
    alias_counts: Counter[str],
) -> tuple[dict[str, object] | None, str | None]:
    collision_scopes: list[str] = []
    for key in skill_lookup_keys(skill):
        if alias_counts.get(key, 0) > 1:
            if key in store:
                collision_scopes.append(key.split(":", 1)[0])
            continue
        record = store.get(key)
        if record is not None:
            return record, None
    if collision_scopes:
        ordered_scopes = ", ".join(sorted(set(collision_scopes)))
        return None, f"ambiguous {ordered_scopes} evidence; provide path, namespace, or source"
    return None, None


def skill_display_name(skill: dict[str, object], alias_counts: Counter[str]) -> str:
    name = str(skill["name"])
    if alias_counts.get(f"name:{name}", 0) <= 1:
        return name
    namespace = str(skill.get("namespace") or "")
    if namespace and namespace not in {"system", "user", "other"}:
        return f"{name}@{namespace}"
    parent_hint = normalize_name(Path(str(skill["path"])).parent.name)
    if parent_hint and parent_hint not in {"skills", ".system"}:
        return f"{name}@{parent_hint}"
    return f"{name}@{skill['source']}"
