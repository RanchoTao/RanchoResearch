"""Research-state schema lookup in source and installed wheel layouts."""

from pathlib import Path
import shutil
import tomllib

from autoresearch_state import validation


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_NAME = "research_state_v0.1.schema.json"


def test_wheel_includes_the_normative_schema():
    config = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    includes = config["tool"]["hatch"]["build"]["targets"]["wheel"]["force-include"]
    assert includes[f"schemas/{SCHEMA_NAME}"] == f"autoresearch_state/schemas/{SCHEMA_NAME}"


def test_schema_works_without_a_repository_root(tmp_path, monkeypatch):
    package_dir = tmp_path / "site-packages" / "autoresearch_state"
    resource = package_dir / "schemas" / SCHEMA_NAME
    resource.parent.mkdir(parents=True)
    shutil.copyfile(ROOT / "schemas" / SCHEMA_NAME, resource)
    monkeypatch.setattr(validation, "__file__", str(package_dir / "validation.py"))

    assert not (package_dir.parent / "schemas").exists()
    assert validation.default_schema_path() == resource
    state = validation.load_state(ROOT / "tests" / "fixtures" / "research_state_generic.yaml")
    assert validation.validate_state(state) == []


def test_source_schema_location_remains_compatible(tmp_path, monkeypatch):
    source_root = tmp_path / "source"
    schema_path = source_root / "schemas" / SCHEMA_NAME
    schema_path.parent.mkdir(parents=True)
    shutil.copyfile(ROOT / "schemas" / SCHEMA_NAME, schema_path)
    monkeypatch.setattr(validation, "__file__", str(source_root / "autoresearch_state" / "validation.py"))

    assert validation.default_schema_path() == schema_path
    assert validation.load_schema()["properties"]["schema_version"]["const"] == "0.1.0"
