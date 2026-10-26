"""The template registry, ported from templates/index.ts.

The render functions produce XeTeX sources; the compile module (coming later)
runs Tectonic over them and caches the PDFs.
"""

from collections.abc import Callable
from dataclasses import dataclass

from resumes.content import ResumeContent

from .banking import render_banking
from .campus import render_campus
from .consulting import render_consulting
from .data_analyst import render_data_analyst
from .designer import render_designer
from .developer import render_developer
from .executive import render_executive
from .finance import render_finance
from .jake import render_jake
from .layout import ResumeLayout
from .marketing import render_marketing
from .ml_research import render_ml_research
from .modern import render_modern
from .product_manager import render_product_manager
from .sb2nov import render_sb2nov


@dataclass(frozen=True)
class TemplateDefinition:
    id: str
    name: str
    description: str
    ats_safe: bool
    version: int
    render: Callable[[ResumeContent, ResumeLayout | None], str]


TEMPLATES: list[TemplateDefinition] = [
    TemplateDefinition(
        id="developer",
        name="Developer",
        description="The Jake's Resume variant most developers use: icon header, dense layout, company above role.",
        ats_safe=True,
        version=1,
        render=render_developer,
    ),
    TemplateDefinition(
        id="jake",
        name="Jake's Resume",
        description="Classic single-column layout popular with software engineers.",
        ats_safe=True,
        version=1,
        render=render_jake,
    ),
    TemplateDefinition(
        id="sb2nov",
        name="Compact",
        description="Denser single-column layout with contact details on the right.",
        ats_safe=True,
        version=1,
        render=render_sb2nov,
    ),
    TemplateDefinition(
        id="modern",
        name="Modern",
        description="Sans-serif, accent-colored headings, inspired by Awesome-CV.",
        ats_safe=True,
        version=1,
        render=render_modern,
    ),
    TemplateDefinition(
        id="ml-research",
        name="Research",
        description=(
            "Serif CV with small-caps headings and numbered, citation-style publications, "
            "for ML engineers and researchers."
        ),
        ats_safe=True,
        version=1,
        render=render_ml_research,
    ),
    TemplateDefinition(
        id="data-analyst",
        name="Analyst",
        description=(
            "Dense sans-serif layout with accent-bar headings and a key and value skills block, "
            "for data scientists and analysts."
        ),
        ats_safe=True,
        version=1,
        render=render_data_analyst,
    ),
    TemplateDefinition(
        id="product-manager",
        name="Product",
        description=(
            "Roomy, outcome-first layout with a bold header rule and square bullets, for product managers."
        ),
        ats_safe=True,
        version=1,
        render=render_product_manager,
    ),
    TemplateDefinition(
        id="designer",
        name="Designer",
        description=(
            "Two-column layout with a sidebar for contact, skills and education, for UI/UX and product "
            "designers; columns may not parse well in ATS."
        ),
        ats_safe=False,
        version=1,
        render=render_designer,
    ),
    TemplateDefinition(
        id="campus",
        name="Campus",
        description=(
            "Campus placement format with education first as a degree, institution, score and year table, "
            "and shaded section bars."
        ),
        ats_safe=True,
        version=1,
        render=render_campus,
    ),
    TemplateDefinition(
        id="banking",
        name="Investment Banking",
        description=(
            "Dense one-page Wall Street layout: serif type, bold firm names, locations and dates on the "
            "right, education first."
        ),
        ats_safe=True,
        version=1,
        render=render_banking,
    ),
    TemplateDefinition(
        id="finance",
        name="Finance & Accounting",
        description=(
            "Classic serif with navy headings and your credentials under the name, certifications near the top."
        ),
        ats_safe=True,
        version=1,
        render=render_finance,
    ),
    TemplateDefinition(
        id="consulting",
        name="Consulting",
        description=(
            "Clean one-page sans-serif layout with ruled headings and square bullets for impact-first results."
        ),
        ats_safe=True,
        version=1,
        render=render_consulting,
    ),
    TemplateDefinition(
        id="marketing",
        name="Marketing & Sales",
        description=(
            "Friendly sans-serif with a warm accent color, a tagline under your name and the summary up top."
        ),
        ats_safe=True,
        version=1,
        render=render_marketing,
    ),
    TemplateDefinition(
        id="executive",
        name="Executive",
        description=(
            "Elegant Garamond layout with summary and core competencies first, roles grouped by company "
            "and board roles."
        ),
        ats_safe=True,
        version=1,
        render=render_executive,
    ),
]


def find_template(template_id: str) -> TemplateDefinition | None:
    return next((t for t in TEMPLATES if t.id == template_id), None)
