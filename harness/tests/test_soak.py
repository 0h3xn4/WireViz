"""M7: a short soak run in CI; `python -m tools.soak 5000 <seed>` runs the long one."""

import pytest

from tools.soak import run_soak


@pytest.mark.parametrize("seed", [11, 12])
def test_random_editing_keeps_every_invariant(seed: int, tmp_path) -> None:  # type: ignore[no-untyped-def]
    r = run_soak(400, seed, tmp_path)
    assert r.steps == 400 and r.applied > 100 and r.generations > 5 and r.roundtrips >= 7
