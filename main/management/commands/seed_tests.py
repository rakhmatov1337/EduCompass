import random
from django.core.management.base import BaseCommand
from django.utils.crypto import get_random_string
from main.models import Level
from quiz.models import Pack, Question, Answer


class Command(BaseCommand):
    help = (
        "Seed the database with logical English questions "
        "(grammar, vocab, preposition) across 2 packs for 'Beginner' level"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=50,
            help='Total number of questions to create (default: 50)'
        )

    def handle(self, *args, **options):
        count = options['count']
        level = Level.objects.filter(name__iexact="Beginner").first()
        if not level:
            self.stderr.write(self.style.ERROR(
                "No Level named 'Beginner' found in the database."))
            return

        # 1) Create 2 Packs
        packs = []
        for i in range(2):
            pack = Pack.objects.create(
                level=level,
                title=f"Pack {i+1}",
                description=f"Logical questions pack {i+1} for level {level.name}"
            )
            packs.append(pack)
            self.stdout.write(self.style.SUCCESS(
                f"Created Pack #{pack.id}: {pack.title}"
            ))

        # 2) Prepare templates
        grammar = [
            ("She ___ to school every day.", ["go", "goes", "going", "gone"], 1),
            ("They ___ playing football now.", ["is", "are", "was", "be"], 1),
            ("He ___ a doctor.", ["am", "is", "are", "were"], 1),
            ("I ___ tea in the morning.", ["drinks", "drink", "drunk", "drinking"], 1),
            ("We ___ our homework yesterday.", ["do", "did", "done", "doing"], 1),
        ]
        vocab = [
            ("What is the synonym of 'happy'?", ["sad", "joyful", "angry", "tired"], 1),
            ("What is the antonym of 'cold'?", ["freezing", "chilly", "hot", "cool"], 2),
            ("Choose the synonym of 'big'", ["huge", "tiny", "thin", "light"], 0),
        ]
        prep = [
            ("I am good ___ math.", ["in", "of", "at", "for"], 2),
            ("The cat is ___ the table.", ["on", "in", "under", "between"], 2),
        ]
        templates = grammar + vocab + prep

        # 3) Build randomized list of exactly count items
        pool = templates * ((count // len(templates)) + 1)
        random.shuffle(pool)
        selected = pool[:count]

        # 4) Create questions, round-robin assign to packs
        for idx, (text, options, correct_idx) in enumerate(selected):
            pack = packs[idx % 2]
            position = Question.objects.filter(pack=pack).count() + 1
            q = Question.objects.create(
                pack=pack,
                text=text,
                position=position
            )
            for opt_idx, opt in enumerate(options):
                Answer.objects.create(
                    question=q,
                    text=opt,
                    correct=(opt_idx == correct_idx)
                )
            self.stdout.write(self.style.SUCCESS(
                f"[{pack.title}] Created Q#{q.id}: \"{text[:30]}…\""
            ))

        self.stdout.write(self.style.SUCCESS(
            f"Successfully seeded {count} logical questions "
            f"across 2 packs for level '{level.name}' (ID: {level.id})."
        ))
