"""Fixture versionnée du contrat de retour de Pythos."""
from pathlib import Path
import json

import pytest

from pyprojectkit import InvalidValue
from pyprojectkit.m2 import ExecutionReportDTO, UnsupportedContractVersion


def test_report_v1_fixture_roundtrip_and_stable_fingerprint() -> None:
    payload = (Path(__file__).parent / "fixtures" / "m2b_execution_report_v1.json").read_text("utf-8")
    report = ExecutionReportDTO.from_json(payload)
    assert report.reported_status == "QUALIFIED"
    assert report.outcome == "SUCCEEDED"
    assert report.fingerprint() == ExecutionReportDTO.from_json(report.to_json()).fingerprint()


def test_report_v1_fixture_rejects_unknown_fields_and_version() -> None:
    data = json.loads((Path(__file__).parent / "fixtures" /
                       "m2b_execution_report_v1.json").read_text("utf-8"))
    data["schema_version"] = "2.0"
    with pytest.raises(UnsupportedContractVersion):
        ExecutionReportDTO.from_dict(data)
    data["schema_version"] = "1.0"
    data["is_human_approved"] = True
    with pytest.raises(InvalidValue):
        ExecutionReportDTO.from_dict(data)
