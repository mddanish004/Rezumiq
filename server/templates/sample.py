"""Realistic content that exercises every section type, ported from sample.ts.
Used to warm the TeX cache and in tests."""

from resumes.content import ResumeContent

SAMPLE_RESUME = ResumeContent.model_validate(
    {
        "basics": {
            "name": "Aarav Sharma",
            "headline": "Backend Engineer",
            "email": "aarav@example.com",
            "phone": "+91 98765 43210",
            "location": "Bengaluru",
            "links": [
                {"label": "LinkedIn", "url": "https://linkedin.com/in/aarav"},
                {"label": "Github", "url": "https://github.com/aarav"},
                {"label": "Portfolio", "url": "https://aarav.dev"},
            ],
        },
        "sections": [
            {
                "id": "skills",
                "type": "skills",
                "title": "Technical Skills",
                "groups": [
                    {"id": "g1", "name": "Languages", "items": ["TypeScript", "Go", "C++"]},
                    {
                        "id": "g2",
                        "name": "Frameworks & Tools",
                        "items": ["Node.js", "Express", "Docker", "PostgreSQL"],
                    },
                ],
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
                        "bullets": [
                            {
                                "id": "b1",
                                "text": "Cut p99 latency of the **payouts API** by 40% using Go & Redis caching",
                            }
                        ],
                    }
                ],
            },
            {
                "id": "proj",
                "type": "projects",
                "title": "Projects",
                "entries": [
                    {
                        "id": "p1",
                        "name": "Resume Builder",
                        "technologies": ["TypeScript", "Postgres"],
                        "links": [{"label": "Live", "url": "https://example.com"}],
                        "start": "2026-09",
                        "end": "present",
                        "bullets": [
                            {
                                "id": "b2",
                                "text": "Compile pipeline with $0 infra cost ~ 1.2s p95 (#perf)",
                            }
                        ],
                    }
                ],
            },
            {
                "id": "edu",
                "type": "education",
                "title": "Education",
                "entries": [
                    {
                        "id": "d1",
                        "institution": "IIT Delhi",
                        "degree": "B.Tech",
                        "field": "Computer Science",
                        "score": "CGPA: 8.9",
                        "location": "New Delhi",
                        "start": "2022",
                        "end": "2026",
                    }
                ],
            },
            {
                "id": "ach",
                "type": "list",
                "title": "Achievements",
                "entries": [{"id": "a1", "title": "Codeforces Expert", "date": "2025"}],
            },
            {
                "id": "links",
                "type": "links",
                "title": "Profile Links",
                "links": [{"label": "Leetcode", "url": "https://leetcode.com/aarav"}],
            },
        ],
    }
)
