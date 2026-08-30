from neo.core.hardware import detect_hardware


def test_detect_hardware_returns_sane_values() -> None:
    hardware = detect_hardware()
    assert hardware.cpu_count >= 1
    assert hardware.ram_total_gb > 0
    assert 0 <= hardware.cpu_load_percent <= 100
    assert 0 <= hardware.ram_load_percent <= 100
