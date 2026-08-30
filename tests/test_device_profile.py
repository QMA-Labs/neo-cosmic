import json

from neo.device import DeviceProfiler


def test_profile_capture_and_atomic_save(tmp_path) -> None:
    profiler = DeviceProfiler()
    profile = profiler.capture()
    assert len(profile.machine_id) == 20
    assert profile.operating_system
    assert profile.cpu_model
    target = profiler.save(profile, tmp_path)
    stored = json.loads(target.read_text(encoding="utf-8"))
    assert stored["machine_id"] == profile.machine_id
    assert not target.with_suffix(".tmp").exists()
