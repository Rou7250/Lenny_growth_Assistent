"""Parses <artifact type="..." title="..."> blocks out of LLM output for the artifact viewer."""
import re

ARTIFACT_RE = re.compile(
    r'<artifact\s+type="(?P<type>markdown|html)"\s+title="(?P<title>[^"]*)"\s*>(?P<content>.*?)</artifact>',
    re.DOTALL,
)


def extract_artifact(text: str) -> dict | None:
    match = ARTIFACT_RE.search(text)
    if not match:
        return None
    return {
        "artifact_type": match.group("type"),
        "title": match.group("title"),
        "content": match.group("content").strip(),
    }


def strip_artifact_tags(text: str) -> str:
    return ARTIFACT_RE.sub("", text).strip()
