SKILL_ONTOLOGY_VERSION = "skills-v2"

SKILL_ALIASES = {
    "amazon ec2": "ec2",
    "amazon web services": "aws",
    "argocd": "argo cd",
    "c sharp": "c#",
    "golang": "go",
    "google cloud platform": "gcp",
    "k8s": "kubernetes",
    "mongo": "mongodb",
    "nestjs": "nest.js",
    "nextjs": "next.js",
    "node": "node.js",
    "nodejs": "node.js",
    "postgres": "postgresql",
    "pydanticai": "pydantic ai",
    "react.js": "react",
    "reactjs": "react",
    "rest apis": "rest api",
    "restful api": "rest api",
    "restful apis": "rest api",
    "ts": "typescript",
}


def canonicalize_skill(value: str) -> str:
    """Return a stable comparison key without using unsafe substring matching."""
    normalized = " ".join(value.casefold().split())
    return SKILL_ALIASES.get(normalized, normalized)
