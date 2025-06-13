import json
from django.core.management.base import BaseCommand
from main.models import Unit, QuizType, Quiz, Question, Answer


class Command(BaseCommand):
    help = "Seed a 50-question beginner English quiz into the database"

    def handle(self, *args, **options):
        # 1. Ensure Unit 1 exists
        unit, _ = Unit.objects.get_or_create(
            number=1,
            defaults={
                'title': 'Basic English',
                'description': 'An introductory quiz covering fundamental grammar and vocabulary.'
            }
        )

        # 2. Ensure the 'Multiple Choice' QuizType exists
        quiz_type, _ = QuizType.objects.get_or_create(
            name='Multiple Choice',
            defaults={'description': 'Select the single best answer.'}
        )

        # 3. Prepare a valid Quill delta for the description
        quill_delta = json.dumps([
            {"insert": "50 multiple-choice questions for absolute beginners.\n"}
        ])

        # 4. Create (or retrieve) the Quiz
        quiz, created = Quiz.objects.get_or_create(
            unit=unit,
            quiz_type=quiz_type,
            name='Beginners English Quiz (50 Questions)',
            defaults={
                'topic': 'Mixed Basics',
                'description': quill_delta,
                'points': 50,
                'show_select': True
            }
        )

        # 5. Define all 50 questions
        questions_data = [
            {'text': "Choose the correct article: ___ apple",
             'choices': ["A", "An", "The", "(no article)"], 'correct': 1},
            {'text': "Choose the correct article: ___ banana",
             'choices': ["The", "An", "A", "(no article)"], 'correct': 2},
            {'text': "What is the plural of 'mouse'?",
             'choices': ["mouses", "mice", "mouse", "mices"], 'correct': 1},
            {'text': "What is the plural of 'child'?",
             'choices': ["childs", "children", "child", "childer"], 'correct': 1},
            {'text': "He ___ a teacher.",
             'choices': ["are", "is", "am", "be"], 'correct': 1},
            {'text': "They ___ playing football.",
             'choices': ["is", "are", "am", "be"], 'correct': 1},
            {'text': "I ___ excited.",
             'choices': ["am", "is", "are", "be"], 'correct': 0},
            {'text': "She is ___ school.",
             'choices': ["at", "in", "on", "to"], 'correct': 0},
            {'text': "We meet ___ Monday.",
             'choices': ["in", "on", "at", "to"], 'correct': 1},
            {'text': "He lives ___ London.",
             'choices': ["in", "at", "on", "to"], 'correct': 0},
            {'text': "The sky is ___.",
             'choices': ["blue", "red", "green", "yellow"], 'correct': 0},
            {'text': "Choose the opposite of 'hot':",
             'choices': ["cold", "warm", "cool", "freeze"], 'correct': 0},
            {'text': "Today is ___.",
             'choices': ["Monday", "Sunday", "Yesterday", "Tomorrow"], 'correct': 0},
            {'text': "___ is the first month of the year.",
             'choices': ["January", "March", "May", "December"], 'correct': 0},
            {'text': "8 is spelled ___.",
             'choices': ["eight", "ate", "ight", "eigth"], 'correct': 0},
            {'text': "This is ___ book.",
             'choices': ["he", "she", "his", "him"], 'correct': 2},
            {'text': "That is ___ bag.",
             'choices': ["her", "she", "hers", "his"], 'correct': 0},
            {'text': "___ is your name?",
             'choices': ["Who", "What", "Where", "When"], 'correct': 1},
            {'text': "___ are you from?",
             'choices': ["Where", "Who", "When", "What"], 'correct': 0},
            {'text': "___ do you do?",
             'choices': ["What", "Who", "Where", "When"], 'correct': 0},
            {'text': "I like tea ___ coffee.",
             'choices': ["and", "or", "but", "so"], 'correct': 0},
            {'text': "I ___ not like fish.",
             'choices': ["do", "don't", "does", "doesn't"], 'correct': 1},
            {'text': "She ___ swim.",
             'choices': ["can", "can't", "able", "must"], 'correct': 0},
            {'text': "You ___ go now.",
             'choices': ["must", "mustn't", "can", "should"], 'correct': 0},
            {'text': "___ a cat on the roof.",
             'choices': ["There is", "There are", "It's", "There"], 'correct': 0},
            {'text': "___ five apples on the table.",
             'choices': ["There is", "There are", "There were", "There"], 'correct': 1},
            {'text': "She is ___ than me.",
             'choices': ["taller", "tallest", "more tall", "most tall"], 'correct': 0},
            {'text': "He is the ___ in the class.",
             'choices': ["tall", "taller", "tallest", "most tall"], 'correct': 2},
            {'text': "I ___ a letter yesterday.",
             'choices': ["write", "wrote", "writed", "written"], 'correct': 1},
            {'text': "They ___ the movie.",
             'choices': ["seen", "saw", "seed", "see"], 'correct': 1},
            {'text': "She ___ eating breakfast.",
             'choices': ["is", "are", "am", "be"], 'correct': 0},
            {'text': "I ___ at home last night.",
             'choices': ["stay", "stayed", "staying", "stayeded"], 'correct': 1},
            {'text': "I ___ going to travel next week.",
             'choices': ["am", "is", "are", "be"], 'correct': 0},
            {'text': "She ___ call you tomorrow.",
             'choices': ["will", "is", "are", "am"], 'correct': 0},
            {'text': "I have ___ water.",
             'choices': ["much", "many", "a few", "few"], 'correct': 0},
            {'text': "I have ___ friends.",
             'choices': ["much", "many", "a few", "little"], 'correct': 1},
            {'text': "He ___ goes to school by bus.",
             'choices': ["always", "sometimes", "never", "often"], 'correct': 0},
            {'text': "Choose synonym of 'big':",
             'choices': ["large", "small", "tiny", "short"], 'correct': 0},
            {'text': "Choose antonym of 'hot':",
             'choices': ["warm", "cold", "cool", "freeze"], 'correct': 1},
            {'text': "It's cold today, ___?",
             'choices': ["isn't it", "aren't they", "doesn't it", "didn't it"], 'correct': 0},
            {'text': "You like coffee, ___?",
             'choices': ["don't you", "aren't you", "didn't you", "won't you"], 'correct': 0},
            {'text': "I ___ seen that movie.",
             'choices': ["have", "has", "had", "having"], 'correct': 0},
            {'text': "She ___ finished her work.",
             'choices': ["hasn't", "haven't", "hadn't", "doesn't"], 'correct': 0},
            {'text': "___ your hands before eating.",
             'choices': ["Wash", "Washes", "Washs", "Washing"], 'correct': 0},
            {'text': "I enjoy ___ music.",
             'choices': ["listen", "listening", "to listen", "listened"], 'correct': 1},
            {'text': "I want ___ a doctor.",
             'choices': ["be", "to be", "being", "been"], 'correct': 1},
        ]

        # 6. Only seed if newly created or empty
        if created or not quiz.questions.exists():
            for idx, qd in enumerate(questions_data, start=1):
                q = Question.objects.create(
                    quiz=quiz,
                    position=idx,
                    text=qd['text']
                )
                answers = [
                    Answer(
                        question=q,
                        position=pos,
                        text=choice,
                        correct=(pos - 1) == qd['correct']
                    )
                    for pos, choice in enumerate(qd['choices'], start=1)
                ]
                Answer.objects.bulk_create(answers)

            self.stdout.write(self.style.SUCCESS("✅ Seeded 50 questions!"))
        else:
            self.stdout.write(self.style.WARNING("Quiz already seeded; skipping."))
