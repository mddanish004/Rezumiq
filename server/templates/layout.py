"""Per-resume layout presets, ported from templates/layout.ts."""

import re
from typing import Literal

from api.common.models import ApiModel


class ResumeLayout(ApiModel):
    spacing: Literal["compact", "normal", "relaxed"] = "normal"
    font_size: Literal[10, 11, 12] | None = None
    links: Literal["icon-and-link", "icon-and-name", "link"] | None = None


PRESETS = {
    "compact": {
        "lineSpread": 0.95,
        "sectionBefore": 2.6,
        "sectionAfter": 1.6,
        "itemGap": -1,
        "nameGap": -3,
    },
    "relaxed": {
        "lineSpread": 1.08,
        "sectionBefore": 4.4,
        "sectionAfter": 2.8,
        "itemGap": 2,
        "nameGap": 4,
    },
}


def preset(layout: ResumeLayout | None) -> dict | None:
    if layout and layout.spacing != "normal":
        return PRESETS[layout.spacing]
    return None


def name_gap_pt(layout: ResumeLayout | None) -> int:
    """Extra space between the name and the line below it, in points."""
    p = preset(layout)
    return p["nameGap"] if p else 0


def name_gap(layout: ResumeLayout | None) -> str:
    pt = name_gap_pt(layout)
    return rf"\vspace{{{pt}pt}}" if pt else ""


def apply_layout(tex: str, layout: ResumeLayout | None) -> str:
    """Applies the font size and spacing to a rendered template. The default
    layout leaves it untouched."""
    out = tex
    if layout and layout.font_size:
        out = re.sub(r"^(\\documentclass\[[^\]]*?)[\d.]+pt\]", rf"\g<1>{layout.font_size}pt]", out)
    p = preset(layout)
    if p:
        lines = [
            rf"\linespread{{{p['lineSpread']}}}",
            rf"\titlespacing*{{\section}}{{0pt}}{{*{p['sectionBefore']}}}{{*{p['sectionAfter']}}}",
            "\\setlist[itemize]{itemsep=\\dimexpr\\itemsep"
            + ("" if p["itemGap"] < 0 else "+")
            + str(p["itemGap"])
            + "pt\\relax}",
        ]
        out = out.replace("\\begin{document}", "\n".join(lines) + "\n\\begin{document}", 1)
    return out
