import io

import yaml
from scicodewiki import hookcheck

from test_verify import DRIFT_IMPL, PASS_IMPL, _write_formulas


def _run_check(tmp_path, edited):
    formulas = _write_formulas(tmp_path, PASS_IMPL)
    import contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        hookcheck.check_edit({"tool_input": {"file_path": str(edited)},
                              "cwd": str(tmp_path)})
    return buf.getvalue(), formulas


def test_unrelated_edit_silent(tmp_path):
    out, _ = _run_check(tmp_path, tmp_path / "src" / "other.py")
    assert out == ""


def test_bound_edit_passes(tmp_path):
    out, _ = _run_check(tmp_path, tmp_path / "src" / "m.py")
    assert "still equivalent" in out


def test_bound_edit_broken_feeds_diagnosis(tmp_path):
    formulas = _write_formulas(tmp_path, DRIFT_IMPL)
    import contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        hookcheck.check_edit({"tool_input": {"file_path": str(tmp_path / "src" / "m.py")},
                              "cwd": str(tmp_path)})
    out = buf.getvalue()
    assert "your edit breaks" in out and "3! = 6" in out
