from neo.app.metrics import MetricsSampler


def test_live_metrics_are_sane(tmp_path) -> None:
    metrics = MetricsSampler(tmp_path).sample()
    assert 0 <= metrics.cpu_percent <= 100
    assert 0 <= metrics.ram_percent <= 100
    assert 0 <= metrics.storage_percent <= 100
    assert metrics.network_down_mbps >= 0
    assert metrics.network_up_mbps >= 0
    assert metrics.gpu_percent is None or 0 <= metrics.gpu_percent <= 100
    assert metrics.vram_used_gb is None or metrics.vram_used_gb >= 0
