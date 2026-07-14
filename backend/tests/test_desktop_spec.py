from pathlib import Path


def test_spec_file_uses_specpath_not_file():
    spec_path = Path("desktop/mem_biosensors.spec")
    spec_content = spec_path.read_text(encoding="utf-8")

    assert "__file__" not in spec_content, "spec file should not use __file__"
    assert "SPECPATH" in spec_content, "spec file should use SPECPATH"
    assert "Path(SPECPATH).resolve().parent" in spec_content
