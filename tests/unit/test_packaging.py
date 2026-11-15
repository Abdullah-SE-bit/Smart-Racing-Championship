import importlib.util
import sys
import zipfile
from pathlib import Path


def test_submission_packager_creates_a_readable_local_zip(tmp_path, monkeypatch):
    script = Path(__file__).resolve().parents[2] / "scripts" / "package_submission.py"
    spec = importlib.util.spec_from_file_location("package_submission", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "ROOT", tmp_path)
    for directory in module.INCLUDED_DIRS:
        (tmp_path / directory).mkdir()
        (tmp_path / directory / "example.txt").write_text(directory)
    for name in module.ROOT_FILES:
        (tmp_path / name).write_text(name)
    (tmp_path / "dist").mkdir()
    (tmp_path / "output" / "pdf").mkdir(parents=True)
    (tmp_path / "dist" / "SmartRacingChampionship.exe").write_bytes(b"test executable fixture")
    (tmp_path / "output" / "pdf" / "technical-report.pdf").write_bytes(b"test report fixture")
    monkeypatch.setattr(sys, "argv", [str(script), "--registration", "24I-0001", "--section", "A"])
    module.main()
    with zipfile.ZipFile(tmp_path / "dist" / "24I-0001_A.zip") as archive:
        assert archive.testzip() is None
        assert "SmartRacingChampionship.exe" in archive.namelist()
        assert "technical-report.pdf" in archive.namelist()
        assert "source/src/example.txt" in archive.namelist()
