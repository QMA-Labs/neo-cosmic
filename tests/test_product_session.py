from pathlib import Path

from neo.bootstrap import bootstrap
from neo.core.config import Settings
from neo.product import ProductSession


def test_consent_is_per_machine_and_revocable(tmp_path: Path) -> None:
    runtime = bootstrap(Settings(data_dir=tmp_path / "data"))
    session = ProductSession(runtime)
    consent = session.save_consent(
        "machine-a",
        device_profile=True,
        discovery_roots=(tmp_path / "Documents",),
        agent_actions=("git_status",),
    )
    assert consent.machine_id == "machine-a"
    assert session.consent_for("machine-b") is None
    assert session.consent_for("machine-a").agent_actions == ("git_status",)  # type: ignore[union-attr]
    assert session.revoke("machine-a") is True
    assert session.consent_for("machine-a") is None
