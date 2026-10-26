from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from latex.tectonic import create_tectonic
from resumes.content import ResumeContent
from templates import TEMPLATES

SAMPLE_CONTENT = {
    "basics": {
        "name": "Aarav Sharma",
        "headline": "Backend Engineer",
        "email": "aarav@example.com",
        "phone": "+91 90000 00000",
        "location": "Bengaluru, India",
        "links": [
            {"label": "GitHub", "url": "https://github.com/aarav"},
            {"label": "LinkedIn", "url": "https://linkedin.com/in/aarav"},
        ],
    },
    "sections": [
        {
            "id": "summary",
            "type": "summary",
            "title": "Summary",
            "text": "Backend engineer with **five years** of experience.",
        },
        {
            "id": "exp",
            "type": "experience",
            "title": "Experience",
            "entries": [
                {
                    "id": "e1",
                    "organization": "Razorpay",
                    "role": "SDE Intern",
                    "location": "Bengaluru",
                    "start": "2025-05",
                    "end": "2025-07",
                    "bullets": [{"id": "b1", "text": "Cut **latency** by 40%"}],
                }
            ],
        },
        {
            "id": "edu",
            "type": "education",
            "title": "Education",
            "entries": [
                {
                    "id": "ed1",
                    "institution": "IIT Bombay",
                    "degree": "B.Tech",
                    "field": "Computer Science",
                    "start": "2021",
                    "end": "2025",
                    "score": "8.9",
                }
            ],
        },
        {
            "id": "projects",
            "type": "projects",
            "title": "Projects",
            "entries": [
                {
                    "id": "p1",
                    "name": "Rezumiq",
                    "url": "https://rezumiq.com",
                    "technologies": ["Django", "React"],
                    "start": "2025-01",
                    "end": "present",
                    "bullets": [{"id": "pb1", "text": "Built a resume builder."}],
                }
            ],
        },
        {
            "id": "skills",
            "type": "skills",
            "title": "Skills",
            "groups": [
                {"id": "s1", "name": "Languages", "items": ["Python", "TypeScript"]},
            ],
        },
        {
            "id": "links",
            "type": "links",
            "title": "Links",
            "links": [{"label": "Portfolio", "url": "https://aarav.dev"}],
        },
        {
            "id": "awards",
            "type": "list",
            "title": "Awards",
            "entries": [
                {"id": "a1", "title": "Dean's List", "subtitle": "IIT Bombay", "date": "2024"},
            ],
        },
    ],
}


class Command(BaseCommand):
    help = "Compiles every template once to warm the Tectonic package cache."

    def handle(self, *args, **options):
        content = ResumeContent.model_validate(SAMPLE_CONTENT)
        compile_tex = create_tectonic(
            bin_path=settings.TECTONIC_BIN,
            only_cached=False,
            timeout_ms=settings.COMPILE_TIMEOUT_MS,
            concurrency=1,
        )
        for definition in TEMPLATES:
            result = compile_tex(definition.render(content, None))
            if not result.get("ok"):
                messages = "; ".join(error["message"] for error in result.get("errors", []))
                raise CommandError(f"{definition.id}: {messages}")
            self.stdout.write(f"Warmed {definition.id}")
