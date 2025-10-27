import datetime
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from .models import Question, Choice


# ---------- MODEL TESTS ----------
class QuestionModelTests(TestCase):
    def test_was_published_recently_with_future_question(self):
        """was_published_recently() returns False for future pub_date."""
        future_time = timezone.now() + datetime.timedelta(days=30)
        future_question = Question(pub_date=future_time)
        self.assertIs(future_question.was_published_recently(), False)

    def test_was_published_recently_with_old_question(self):
        """was_published_recently() returns False for questions older than 1 day."""
        old_time = timezone.now() - datetime.timedelta(days=1, seconds=1)
        old_question = Question(pub_date=old_time)
        self.assertIs(old_question.was_published_recently(), False)

    def test_was_published_recently_with_recent_question(self):
        """was_published_recently() returns True for recent questions."""
        recent_time = timezone.now() - datetime.timedelta(
            hours=23, minutes=59, seconds=59
        )
        recent_question = Question(pub_date=recent_time)
        self.assertIs(recent_question.was_published_recently(), True)

    def test_str_methods(self):
        """String representations of models should be readable."""
        q = Question.objects.create(
            question_text="Best framework?", pub_date=timezone.now()
        )
        c = Choice.objects.create(question=q, choice_text="Django", votes=5)
        self.assertEqual(str(q), "Best framework?")
        self.assertEqual(str(c), "Django")


# ---------- VIEW TESTS ----------
class QuestionViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.q1 = Question.objects.create(
            question_text="Past Q1",
            pub_date=timezone.now() - datetime.timedelta(days=1),
        )
        self.q2 = Question.objects.create(
            question_text="Recent Q2", pub_date=timezone.now()
        )

    def test_index_view_status_code_and_template(self):
        """Index page should load and use the correct template."""
        response = self.client.get(reverse("polls:index"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "polls/index.html")

    def test_index_view_context(self):
        """Index view should list recent questions."""
        response = self.client.get(reverse("polls:index"))
        self.assertIn(self.q1, response.context["latest_question_list"])
        self.assertIn(self.q2, response.context["latest_question_list"])

    def test_detail_view_renders_question(self):
        """Detail view should render the correct question."""
        response = self.client.get(reverse("polls:detail", args=(self.q1.id,)))
        self.assertContains(response, self.q1.question_text)
        self.assertEqual(response.status_code, 200)

    def test_results_view_renders_question(self):
        """Results view should show question and choices."""
        Choice.objects.create(question=self.q1, choice_text="Yes", votes=3)
        response = self.client.get(reverse("polls:results", args=(self.q1.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.q1.question_text)


# ---------- VOTE FUNCTION TESTS ----------
class VoteViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.question = Question.objects.create(
            question_text="Favorite language?", pub_date=timezone.now()
        )
        self.choice1 = Choice.objects.create(
            question=self.question, choice_text="Python", votes=0
        )
        self.choice2 = Choice.objects.create(
            question=self.question, choice_text="C++", votes=0
        )

    def test_vote_valid_choice_increments_vote(self):
        """Submitting a valid vote should increase the vote count."""
        url = reverse("polls:vote", args=(self.question.id,))
        response = self.client.post(url, {"choice": self.choice1.id})
        self.choice1.refresh_from_db()
        self.assertEqual(self.choice1.votes, 1)
        self.assertRedirects(
            response, reverse("polls:results", args=(self.question.id,))
        )

    def test_vote_invalid_choice_shows_error(self):
        """Submitting without a valid choice shows an error."""
        url = reverse("polls:vote", args=(self.question.id,))
        response = self.client.post(url, {"choice": 999})  # invalid ID
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "You didn&#x27;t select a choice.")
        self.assertTemplateUsed(response, "polls/detail.html")

    def test_vote_missing_choice_key_shows_error(self):
        """Submitting with no 'choice' key in POST shows error."""
        url = reverse("polls:vote", args=(self.question.id,))
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "You didn&#x27;t select a choice.")
