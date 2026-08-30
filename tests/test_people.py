from neo.memory import MemoryStore
from neo.people import PeopleEngine


def test_people_alias_and_update(tmp_path) -> None:
    engine = PeopleEngine(MemoryStore(tmp_path / "memory.sqlite3"))
    person = engine.create("Sara", aliases=("مامان",), attributes={"color": "purple"})
    assert engine.find("مامان").id == person.id  # type: ignore[union-attr]
    updated = engine.update(person.id, aliases=("Mom",), attributes={"birthday": "03-10"})
    assert updated.attributes == {"color": "purple", "birthday": "03-10"}
    assert engine.find("mom").id == person.id  # type: ignore[union-attr]
    assert len(engine.create("مامان").aliases) == 2


def test_vcard_import_and_owner_proposal(tmp_path, monkeypatch) -> None:
    engine = PeopleEngine(MemoryStore(tmp_path / "memory.sqlite3"))
    profiles = engine.import_vcard(
        "BEGIN:VCARD\nVERSION:3.0\nFN:Sara NEO\nEMAIL:sara@example.com\nTEL:+123\nEND:VCARD"
    )
    assert profiles[0].attributes["emails"] == ("sara@example.com",)
    monkeypatch.setattr("getpass.getuser", lambda: "Masiha")
    proposed = engine.propose_owner()
    assert proposed.confidence == 0.35
    stored = engine.memory.get(f"people.profile.{proposed.id}")
    assert stored is not None and stored.protected is False
