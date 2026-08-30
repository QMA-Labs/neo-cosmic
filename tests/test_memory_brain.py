import pytest

from neo.memory import MemoryKind, MemoryStore


def test_typed_evidence_memory_and_search(tmp_path) -> None:
    store = MemoryStore(tmp_path / "brain.sqlite3")
    entry = store.set(
        "person.mom.color",
        "purple",
        kind=MemoryKind.CORE,
        confidence=0.92,
        protected=True,
        source="user",
        evidence={"quote": "مامان بنفش دوست دارد"},
    )
    assert entry.protected is True
    assert entry.evidence["quote"]
    assert store.search("purple")[0].key == entry.key
    assert store.list(kind=MemoryKind.CORE)[0].kind == "core"


def test_never_forget_requires_force(tmp_path) -> None:
    store = MemoryStore(tmp_path / "brain.sqlite3")
    store.set("identity.owner", "Masiha", kind="core", protected=True)
    with pytest.raises(PermissionError):
        store.forget("identity.owner")
    assert store.forget("identity.owner", force=True)


def test_temporary_memory_expires(tmp_path) -> None:
    store = MemoryStore(tmp_path / "brain.sqlite3")
    store.set("session.context", "temporary", kind="temporary", ttl_seconds=-1)
    assert store.get("session.context") is None


def test_knowledge_graph_relation(tmp_path) -> None:
    store = MemoryStore(tmp_path / "brain.sqlite3")
    store.set("person.mom", {"name": "Mom"})
    store.set("color.purple", "purple")
    relation = store.relate(
        "person.mom", "likes", "color.purple", confidence=0.9, evidence="told by owner"
    )
    assert relation.relation == "likes"
    assert store.relations("person.mom")[0].target_key == "color.purple"
