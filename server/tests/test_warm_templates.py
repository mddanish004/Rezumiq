from unittest.mock import patch

from django.core.management import call_command

from templates import TEMPLATES


def test_warm_templates_compiles_every_template():
    sources = []

    def fake_compile(source, cancel=None):
        sources.append(source)
        return {"ok": True, "pdf": b"%PDF"}

    with patch(
        "resumes.management.commands.warm_templates.create_tectonic",
        return_value=fake_compile,
    ):
        call_command("warm_templates")

    assert len(sources) == len(TEMPLATES)
    assert all("\\documentclass" in source for source in sources)
