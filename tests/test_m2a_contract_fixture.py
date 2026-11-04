"""Compatibilité JSON reproductible du contrat v1."""
from pathlib import Path
from pyprojectkit.m2 import OperatingBriefDTO


def test_v1_contract_fixture_roundtrip() -> None:
    fixture = Path(__file__).parent / "fixtures" / "m2a_operating_brief_v1.json"
    brief = OperatingBriefDTO.from_json(fixture.read_text(encoding="utf-8"))
    assert brief.schema_version == "1.0"
    assert brief.mode == "AUDIT"
    assert brief.target_reference.revision == "a" * 40
    assert OperatingBriefDTO.from_json(brief.to_json()) == brief
