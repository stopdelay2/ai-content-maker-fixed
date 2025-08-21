# anchor_config.py
import json
from typing import Optional, Tuple


def load_rules_and_anchors(
    file_path: str,
    domain: Optional[str] = None,
    anchors_format: str = "lines",  # "lines" | "csv" | "json"
) -> Tuple[str, str]:
    """
    Loads the JSON config at file_path and returns (rules_str, anchors_str) for the given domain.
    rules_str is pretty-printed JSON. anchors_str format is controlled by anchors_format.

    Example:
        rules_str, anchors_str = load_rules_and_anchors("anchors.json", "stopdelay.co.il")
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Config file not found: {file_path}") from e
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {file_path}: {e}") from e

    sites = cfg.get("sites")
    if not isinstance(sites, dict) or not sites:
        raise ValueError("Config must contain a non-empty 'sites' object.")

    # Pick site
    if domain is None:
        if len(sites) == 1:
            domain = next(iter(sites))
        else:
            raise ValueError(f"Multiple sites present; specify domain. Available: {', '.join(sorted(sites))}")

    site_cfg = sites.get(domain)
    if not site_cfg:
        raise ValueError(f"Domain '{domain}' not found. Available: {', '.join(sorted(sites))}")

    rules = site_cfg.get("rules", {})
    if not isinstance(rules, dict):
        raise ValueError(f"'rules' for '{domain}' must be an object.")

    anchors = []
    for a in site_cfg.get("anchors", []):
        if isinstance(a, dict) and "text" in a and str(a["text"]).strip():
            anchors.append(str(a["text"]).strip())
    if not anchors:
        raise ValueError(f"No anchors found for '{domain}'.")

    # Stringify
    rules_str = json.dumps(rules, ensure_ascii=False, indent=2)
    if anchors_format == "json":
        anchors_str = json.dumps(anchors, ensure_ascii=False, indent=2)
    elif anchors_format == "csv":
        anchors_str = ", ".join(anchors)
    else:  # "lines"
        anchors_str = "\n".join(anchors)

    return rules_str, anchors_str


# Optional convenience to get one combined block you can drop into an LLM prompt.
def load_as_prompt(file_path: str, domain: Optional[str] = None, anchors_format: str = "lines") -> str:
    rules_str, anchors_str = load_rules_and_anchors(file_path, domain, anchors_format)
    return f"RULES:\n{rules_str}\n\nANCHORS:\n{anchors_str}\n"
