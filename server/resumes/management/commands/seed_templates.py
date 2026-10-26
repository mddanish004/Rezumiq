"""Syncs template metadata from code into the database, ported from db/seed.ts.

Safe to run on every deploy: rows are upserted by slug. Templates missing from
the registry are left untouched, since a deactivate would break resume rows
that still point at them.
"""

from django.core.management.base import BaseCommand

from resumes.models import Template
from templates import TEMPLATES


class Command(BaseCommand):
    help = "Upserts every template in the registry, in registry order."

    def handle(self, *args, **options):
        for definition in TEMPLATES:
            Template.objects.update_or_create(
                id=definition.id,
                defaults={
                    "name": definition.name,
                    "description": definition.description,
                    "ats_safe": definition.ats_safe,
                    "version": definition.version,
                    "is_active": True,
                },
            )
        self.stdout.write(f"Seeded {len(TEMPLATES)} templates")
