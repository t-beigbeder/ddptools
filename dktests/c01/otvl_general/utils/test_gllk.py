from otvl_general.utils.gllk import GlDict, initialize
import pytest


def test_gldict() -> None:
    initialize()
    GlDict().put("k", "v")
    assert GlDict().get("k") == "v"
    assert GlDict().exists("k")
    GlDict().delete("k")
    assert not GlDict().exists("k")
    with pytest.raises(KeyError):
        _ = GlDict().get("k")
