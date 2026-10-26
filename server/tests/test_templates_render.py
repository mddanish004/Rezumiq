"""Registry and renderer checks for the LaTeX templates."""

from resumes.content import ResumeContent
from templates import TEMPLATES, find_template
from templates.latex import date_range, fits_one_line, tex, tex_rich, tex_url, visible_content
from templates.layout import ResumeLayout, apply_layout, name_gap
from templates.sample import SAMPLE_RESUME

OLD_ORDER = [
    "developer",
    "jake",
    "sb2nov",
    "modern",
    "ml-research",
    "data-analyst",
    "product-manager",
    "designer",
    "campus",
    "banking",
    "finance",
    "consulting",
    "marketing",
    "executive",
]


def test_registry_matches_old_order():
    assert [t.id for t in TEMPLATES] == OLD_ORDER


def test_designer_is_the_only_ats_unsafe_template():
    assert [t.id for t in TEMPLATES if not t.ats_safe] == ["designer"]


def test_find_template():
    assert find_template("jake") is TEMPLATES[1]
    assert find_template("nope") is None


def test_every_template_renders_sample_content():
    for t in TEMPLATES:
        source = t.render(SAMPLE_RESUME, None)
        assert source.count("\\begin{document}") == 1, t.id
        assert source.strip().endswith("\\end{document}"), t.id
        assert "Aarav Sharma" in source, t.id


def test_layout_preset_applied():
    relaxed = ResumeLayout(spacing="relaxed", font_size=12, links="link")
    for t in TEMPLATES:
        source = t.render(SAMPLE_RESUME, relaxed)
        assert "\\linespread{1.08}" in source, t.id
        assert "\\titlespacing*{\\section}{0pt}{*4.4}{*2.8}" in source, t.id
        assert "\\documentclass[" in source and "10.5pt]" not in source, t.id


def test_font_size_replaces_medium_fraction():
    jake = find_template("jake")
    source = jake.render(SAMPLE_RESUME, ResumeLayout(font_size=11))
    assert "\\documentclass[a4paper,11pt]{article}" in source


def test_normal_layout_leaves_font_size_alone():
    jake = find_template("jake")
    assert "\\documentclass[a4paper,11pt]{article}" in jake.render(SAMPLE_RESUME, ResumeLayout())


def test_plain_layout_skips_preset_lines():
    jake = find_template("jake")
    assert "\\linespread" not in jake.render(SAMPLE_RESUME, None)


def test_tex_escapes_specials():
    assert tex("a & b_1") == r"a \& b\_1"
    assert tex(None) == ""
    assert tex(r"back\slash") == r"back\textbackslash{}slash"


def test_tex_rich_keeps_bold_marking():
    assert tex_rich("**payouts API**") == r"\textbf{payouts API}"
    assert tex_rich("[docs](https://x.com/a)") == r"\href{https://x.com/a}{\underline{docs}}"
    assert tex_rich(None) == ""


def test_tex_url_escapes_breakers():
    assert tex_url("https://x.com/a^b#c%1") == r"https://x.com/a%5Eb\#c\%1"


def test_date_ranges():
    assert date_range("2025-06", "2026-01") == "Jun 2025 -- Jan 2026"
    assert date_range("2025", None) == "2025"
    assert date_range("2024-01", "present") == "Jan 2024 -- Present"
    assert date_range(None, None) == ""


def test_fits_one_line_thresholds():
    short = ["a", "b"]
    assert fits_one_line(short, False)
    assert not fits_one_line(["x" * 91], False)
    assert not fits_one_line(["x" * 76], True)


def test_visible_content_drops_hidden_and_shells():
    content = ResumeContent.model_validate(
        {
            "basics": {"name": "A"},
            "sections": [
                {
                    "id": "s1",
                    "type": "skills",
                    "title": "Skills",
                    "groups": [{"id": "g1", "name": "Frontend:", "items": []}],
                },
                {
                    "id": "s2",
                    "type": "list",
                    "title": "Awards",
                    "entries": [
                        {
                            "id": "a1",
                            "title": "kept",
                            "bullets": [{"id": "b1", "text": "kept bullet"}],
                        },
                        {
                            "id": "a2",
                            "title": "gone",
                            "hidden": True,
                            "bullets": [{"id": "b2", "text": "gone bullet"}],
                        },
                    ],
                },
                {"id": "s3", "type": "list", "title": "Hidden", "hidden": True, "entries": []},
            ],
        }
    )
    visible = visible_content(content)
    assert [s.id for s in visible.sections] == ["s2"]
    assert [e.id for e in visible.sections[0].entries] == ["a1"]


def test_name_gap_pt_matches_presets():
    assert name_gap(None) == ""
    assert name_gap(ResumeLayout()) == ""
    assert name_gap(ResumeLayout(spacing="compact")) == r"\vspace{-3pt}"
    assert name_gap(ResumeLayout(spacing="relaxed")) == r"\vspace{4pt}"


def test_apply_layout_inserts_before_document():
    source = "\\documentclass[a4paper,10pt]{article}\n\\begin{document}\nX\n\\end{document}\n"
    out = apply_layout(source, ResumeLayout(spacing="compact"))
    assert out.index("\\linespread{0.95}") < out.index("\\begin{document}")


def test_visible_content_accepts_stored_dict_content():
    from templates.latex import visible_content

    rendered = visible_content(
        {
            "basics": {"name": "Aarav", "links": []},
            "sections": [
                {"type": "summary", "id": "s", "title": "Summary", "hidden": False, "text": "Hi"}
            ],
        }
    )
    assert rendered.basics.name == "Aarav" and rendered.sections[0].text == "Hi"
