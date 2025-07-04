from django.core.management.base import BaseCommand
from main.models import Level
from quiz.models import Question, Answer
import random


class Command(BaseCommand):
    help = "Seed the database with logical English questions (with 4 answers each) for 'Beginner' level"

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=50,
            help='Number of questions to create (default: 50)'
        )

    def handle(self, *args, **options):
        count = options['count']

        level = Level.objects.filter(name__iexact="Beginner").first()
        if not level:
            self.stderr.write(self.style.ERROR(
                "No Level named 'Beginner' found in the database."))
            return

        grammar_templates = [
            ("She ___ to school every day.", ["go", "goes", "going", "gone"], 1),
            ("They ___ playing football now.", ["is", "are", "was", "be"], 1),
            ("He ___ a doctor.", ["am", "is", "are", "were"], 1),
            ("I ___ tea in the morning.", ["drinks", "drink", "drunk", "drinking"], 1),
            ("We ___ our homework yesterday.", ["do", "did", "done", "doing"], 1),
        ]

        vocab_templates = [
            ("What is the synonym of 'happy'?", ["sad", "joyful", "angry", "tired"], 1),
            ("What is the antonym of 'cold'?", [
             "freezing", "chilly", "hot", "cool"], 2),
            ("Choose the synonym of 'big'", ["huge", "tiny", "thin", "light"], 0),
        ]

        preposition_templates = [
            ("I am good ___ math.", ["in", "of", "at", "for"], 2),
            ("The cat is ___ the table.", ["on", "in", "under", "between"], 2),
        ]

        templates = grammar_templates + vocab_templates + preposition_templates

        # Repeat templates if needed to reach count
        full_templates = templates * ((count // len(templates)) + 1)
        random.shuffle(full_templates)
        selected_templates = full_templates[:count]

        created_q = 0
        base_count = Question.objects.filter(level=level).count()

        for i, (q_text, options, correct_idx) in enumerate(selected_templates):
            question = Question.objects.create(
                level=level,
                text=q_text,
                position=base_count + i + 1
            )
            for j, opt in enumerate(options):
                Answer.objects.create(
                    question=question,
                    text=opt,
                    correct=(j == correct_idx)
                )
            created_q += 1
            self.stdout.write(self.style.SUCCESS(
                f"Created logical question #{question.id}"))

        self.stdout.write(self.style.SUCCESS(
            f"Successfully seeded {created_q} logical questions for level 'Beginner' (ID: {level.id})."
        ))
