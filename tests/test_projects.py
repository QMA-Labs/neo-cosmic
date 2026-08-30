import json

from neo.memory import MemoryStore
from neo.projects import ProjectDetector


def test_detects_python_and_node_projects_and_skills(tmp_path) -> None:
    python = tmp_path / "api"
    python.mkdir()
    (python / "pyproject.toml").write_text("[project]\nname='api'", encoding="utf-8")
    (python / "requirements.txt").write_text("fastapi==1.0\n# ignored\n", encoding="utf-8")
    node = tmp_path / "web"
    node.mkdir()
    (node / "package.json").write_text(
        json.dumps({"scripts": {"dev": "vite", "test": "vitest"}, "dependencies": {"vite": "1"}}),
        encoding="utf-8",
    )
    store = MemoryStore(tmp_path / "memory.sqlite3")
    profiles = ProjectDetector(store).discover((tmp_path,))
    by_name = {profile.name: profile for profile in profiles}
    assert "python" in by_name["api"].stack
    assert "pytest" in by_name["api"].test_commands
    assert by_name["web"].run_commands == ("npm run dev",)
    assert store.get(f"skills.project.{by_name['web'].id}") is not None
