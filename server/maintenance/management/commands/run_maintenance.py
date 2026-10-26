"""Run all maintenance tasks once. Schedule via cron/systemd/timer."""

from django.core.management.base import BaseCommand

from maintenance.tasks import TASKS


class Command(BaseCommand):
    help = "Run all maintenance tasks once."

    def add_arguments(self, parser):
        parser.add_argument("task", nargs="?", default="all")

    def handle(self, *args, **options):
        task = options["task"]
        if task == "all":
            for name, fn in TASKS.items():
                self.stdout.write(f"== {name}")
                fn()
        elif task in TASKS:
            TASKS[task]()
        else:
            self.stderr.write(f"Unknown task: {task}")
