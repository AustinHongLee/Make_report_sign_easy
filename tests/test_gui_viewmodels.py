from __future__ import annotations

from pathlib import Path

from Make_report_sign_easy.gui.session import AppSession
from Make_report_sign_easy.gui.viewmodels.batch_vm import BatchViewModel
from Make_report_sign_easy.gui.viewmodels.export_vm import ExportViewModel
from Make_report_sign_easy.gui.viewmodels.template_vm import TemplateViewModel
from Make_report_sign_easy.pdf.models import Field, FillResult, Template, ValueSet
from Make_report_sign_easy.services import BatchFillResult, TemplateInspection


def _template(path: Path) -> Template:
    return Template(
        path=path,
        fields=(
            Field("name", 0, (10, 20, 110, 40)),
            Field("date", 0, (10, 50, 110, 70)),
        ),
    )


class FakeTemplateService:
    def __init__(self, template: Template) -> None:
        self.template = template

    def load_template(self, path: str | Path, *, page_index: int = 0) -> Template:
        return self.template

    def inspect(
        self,
        template_path: str | Path,
        *,
        values: dict | None = None,
        page_index: int = 0,
    ) -> TemplateInspection:
        values = values or {}
        field_keys = set(self.template.field_keys)
        value_keys = set(values)
        return TemplateInspection(
            template=self.template,
            value_keys=tuple(sorted(value_keys)),
            matched_keys=tuple(sorted(field_keys & value_keys)),
            missing_value_keys=tuple(sorted(field_keys - value_keys)),
            extra_value_keys=tuple(sorted(value_keys - field_keys)),
        )


class FakeValueSetService:
    def load_json(self, path: str | Path) -> ValueSet:
        return ValueSet({"name": "Alice"})


class FakeBatchService:
    def __init__(self) -> None:
        self.last_request = None

    def run(self, request):
        self.last_request = request
        return BatchFillResult(
            results=tuple(
                FillResult(item.output_path, filled_fields=("name",), missing_fields=())
                for item in request.items
            )
        )


class FakeDocumentService:
    def __init__(self) -> None:
        self.last_request = None

    def run(self, request):
        self.last_request = request
        return FillResult(request.output_path, filled_fields=("name",), missing_fields=())


def test_template_vm_loads_template_and_tracks_missing_values(tmp_path):
    template = _template(tmp_path / "template.pdf")
    session = AppSession()
    vm = TemplateViewModel(
        session,
        templates=FakeTemplateService(template),
        value_sets=FakeValueSetService(),
    )

    vm.load_template(template.path)

    assert session.template == template
    assert len(session.template.fields) == 2
    assert session.selected_key == "name"
    assert session.inspection is not None
    assert session.inspection.missing_value_keys == ("date", "name")

    vm.set_value("name", "Alice")

    assert session.values == {"name": "Alice"}
    assert session.inspection is not None
    assert session.inspection.matched_keys == ("name",)
    assert session.inspection.missing_value_keys == ("date",)


def test_batch_vm_aggregates_results_and_preserves_item_metadata(tmp_path):
    session = AppSession(template=_template(tmp_path / "template.pdf"), values={"name": "Alice"})
    service = FakeBatchService()
    vm = BatchViewModel(session, batches=service)

    vm.add_current_values(tmp_path / "current.pdf", label="current", seed=7)
    vm.add_values_path(tmp_path / "values.json", tmp_path / "imported.pdf", label="imported", seed=8)
    result = vm.run()

    assert result is not None
    assert session.batch_result == result
    assert result.output_paths == (tmp_path / "current.pdf", tmp_path / "imported.pdf")
    assert service.last_request is not None
    assert [item.label for item in service.last_request.items] == ["current", "imported"]
    assert [item.seed for item in service.last_request.items] == [7, 8]


def test_export_vm_uses_session_and_records_output(tmp_path):
    session = AppSession(template=_template(tmp_path / "template.pdf"), values={"name": "Alice"})
    service = FakeDocumentService()
    vm = ExportViewModel(session, documents=service)

    result = vm.export_pdf(tmp_path / "out.pdf", emit_signal=False)

    assert result is not None
    assert session.last_output_path == tmp_path / "out.pdf"
    assert service.last_request is not None
    assert service.last_request.template_path == session.template.path
    assert service.last_request.values == {"name": "Alice"}
    assert service.last_request.clear_annots is True
