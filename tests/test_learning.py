import pytest

from neo.learning import LearningEngine, LearningEventType
from neo.memory import MemoryStore


def test_correction_and_failure_memory(tmp_path) -> None:
    store = MemoryStore(tmp_path / "memory.sqlite3")
    engine = LearningEngine(store)
    correction = engine.correct("owner.color", "blue", "purple", reason="user said so")
    assert correction.type == LearningEventType.CORRECTION
    learned = store.get("learned.correction.owner.color")
    assert learned is not None and learned.value == "purple"
    failure = engine.failure("build", "exit 1", attempted_action="pytest")
    assert failure.after["error"] == "exit 1"


def test_skill_requires_evidence_and_approval(tmp_path) -> None:
    store = MemoryStore(tmp_path / "memory.sqlite3")
    engine = LearningEngine(store)
    event = engine.workflow("test project", ({"action": "pytest"},), successful=True)
    proposal = engine.propose_skill(
        "Test project", "Run project tests", ({"action": "git_status"},), (event.id,)
    )
    assert proposal.status == "proposed"
    assert store.get(f"learning.skill.{proposal.id}").protected is False  # type: ignore[union-attr]
    approved = engine.approve_skill(proposal.id)
    assert approved.status == "approved"
    assert store.get(f"learning.skill.{proposal.id}").protected is True  # type: ignore[union-attr]
    with pytest.raises(ValueError):
        engine.propose_skill("bad", "no evidence", ({"action": "x"},), ())


def test_consolidation_removes_exact_duplicate_events(tmp_path) -> None:
    store = MemoryStore(tmp_path / "memory.sqlite3")
    engine = LearningEngine(store)
    for _ in range(2):
        engine.record(LearningEventType.FAILURE, "same", before="x", after="y")
    result = engine.consolidate()
    assert result["duplicates_removed"] == 1
