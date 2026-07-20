from evaluation.run_chunk_experiments import VARIANTS


def test_required_chunk_variants_are_defined() -> None:
    assert VARIANTS == [(350, 50), (700, 100), (1200, 150)]
