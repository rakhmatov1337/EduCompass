import json
from django.core.management.base import BaseCommand
from django.db import transaction
from quiz.models import Quiz, Question, Answer, Level


class Command(BaseCommand):
    help = "Seed the database with a 50-question English MCQ quiz for beginners."

    @transaction.atomic
    def handle(self, *args, **options):
        # 1. Beginner level'ni olish yoki yaratish
        level, _ = Level.objects.get_or_create(name="Beginner")

        # 2. Oldingi shu nomdagi quiz va unga oid savollarni o'chirish
        quiz_name = "English Test for Beginners"
        Quiz.objects.filter(name=quiz_name, type=Quiz.QuizType.MULTIPLE_CHOICE).delete()
        self.stdout.write(
            "Oldingi English Test for Beginners o‘chirildi (agar mavjud edi).")
        quiz = Quiz.objects.create(
            name=quiz_name,
            description="",
            level=level,
            type=Quiz.QuizType.MULTIPLE_CHOICE
        )
        self.stdout.write(f"Yangi quiz yaratildi: {quiz.name}")

        # 4. Savol-javob shablonlari
        templates = [
            {
                "text": "Fill in the blank: I ____ a teacher.",
                "answers": [("am", True), ("is", False), ("are", False), ("be", False)],
            },
            {
                "text": "Choose the correct article: __ apple a day keeps the doctor away.",
                "answers": [("An", True), ("A", False), ("The", False), ("Some", False)],
            },
            {
                "text": "What is the plural of 'cat'?",
                "answers": [("cats", True), ("cat", False), ("cates", False), ("cati", False)],
            },
            {
                "text": "Translate to English: 'Salom'.",
                "answers": [("Hello", True), ("Hi", False), ("Hey", False), ("Hola", False)],
            },
            {
                "text": "What is the opposite of 'hot'?",
                "answers": [("cold", True), ("warm", False), ("cool", False), ("heat", False)],
            },
        ]

        # 5. 50 ta savol yaratish
        for i in range(50):
            tpl = templates[i % len(templates)]
            position = i + 1
            question = Question.objects.create(
                quiz=quiz,
                text=tpl["text"],
                position=position
            )
            self.stdout.write(f"{position}. Savol qo‘shildi: {question.text}")

            for j, (ans_text, is_correct) in enumerate(tpl["answers"], start=1):
                answer = Answer.objects.create(
                    question=question,
                    text=ans_text,
                    correct=is_correct,
                    position=j
                )
                mark = "✔" if is_correct else "✘"
                self.stdout.write(f"    {mark} {answer.text}")

        self.stdout.write(self.style.SUCCESS(
            "Seed tugallandi: 50 ta English MCQ savol yaratildi!"
        ))
