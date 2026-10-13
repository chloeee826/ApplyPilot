import pytest

from app.services.skill_ontology import SKILL_ONTOLOGY_VERSION, canonicalize_skill


@pytest.mark.parametrize(
    ("left", "right"),
    [
        ("Postgres", "PostgreSQL"),
        ("React.js", "React"),
        ("Node", "Node.js"),
        ("REST APIs", "REST API"),
        ("Amazon Web Services", "AWS"),
        ("K8s", "Kubernetes"),
        ("TS", "TypeScript"),
        ("Mongo", "MongoDB"),
        ("Golang", "Go"),
        ("C Sharp", "C#"),
        ("Amazon EC2", "EC2"),
        ("ArgoCD", "Argo CD"),
        ("NextJS", "Next.js"),
        ("NestJS", "Nest.js"),
        ("Google Cloud Platform", "GCP"),
        ("PydanticAI", "Pydantic AI"),
    ],
)
def test_known_aliases_share_a_canonical_key(left: str, right: str) -> None:
    assert canonicalize_skill(left) == canonicalize_skill(right)


def test_canonicalization_normalizes_case_and_whitespace() -> None:
    assert canonicalize_skill("  Machine   Learning ") == "machine learning"


def test_false_friends_remain_distinct() -> None:
    assert canonicalize_skill("Java") != canonicalize_skill("JavaScript")
    assert canonicalize_skill("C") != canonicalize_skill("C++")
    assert canonicalize_skill("Next.js") != canonicalize_skill("Nest.js")
    assert canonicalize_skill("Apollo") != canonicalize_skill("Apollo Client")
    assert canonicalize_skill("TanStack Query") != canonicalize_skill("React Query")
    assert canonicalize_skill("Pydantic") != canonicalize_skill("Pydantic AI")


def test_skill_ontology_has_a_persistable_version() -> None:
    assert SKILL_ONTOLOGY_VERSION == "skills-v2"
