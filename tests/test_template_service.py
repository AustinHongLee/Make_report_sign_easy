import json
from pathlib import Path

from Make_report_sign_easy.services import TemplateService, ValueSetService


REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = REPO_ROOT / "samples" / "附件六_管線工程施工自主檢查表.pdf"
VALUES = REPO_ROOT / "samples" / "values_sample.json"
EXPECTED = REPO_ROOT / "tests" / "golden" / "phase0_expected.json"


def test_template_service_reports_phase0_fields():
    expected = json.loads(EXPECTED.read_text(encoding="utf-8"))

    template = TemplateService().load_template(TEMPLATE)

    assert sorted(template.field_keys) == expected["template_field_keys"]
    assert all(field.field_type == "FreeText" for field in template.fields)


def test_template_service_inspects_value_coverage():
    service = TemplateService()
    values = ValueSetService().load_json(VALUES).values

    inspection = service.inspect(TEMPLATE, values=values)

    assert inspection.is_complete
    assert inspection.missing_value_keys == ()
    assert inspection.extra_value_keys == ()
    assert tuple(sorted(inspection.matched_keys)) == tuple(sorted(values.keys()))


def test_template_service_reports_missing_and_extra_values():
    values = dict(ValueSetService().load_json(VALUES).values)
    values.pop("Company_words")
    values["NotInTemplate_words"] = "ignored"

    inspection = TemplateService().inspect(TEMPLATE, values=values)

    assert not inspection.is_complete
    assert inspection.missing_value_keys == ("Company_words",)
    assert inspection.extra_value_keys == ("NotInTemplate_words",)
