from django.db import models
from django.conf import settings
import uuid

class RPMItem(models.Model):
    item_id = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    image = models.ImageField(upload_to='matrices/')
    difficulty = models.IntegerField(choices=[(1,'Easy'), (2,'Medium'), (3,'Hard')])
    correct_answer = models.CharField(max_length=10)
    explanation = models.TextField(blank=True)
    set_number = models.IntegerField(help_text="For fixed levels")
    is_reserved = models.BooleanField(default=False)
    @property
    def points(self):
        """Points according to problem type"""
        return self.set_number

    def __str__(self):
        return f"Item {self.item_id} (Set {self.set_number})"

class TestSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    session_type = models.CharField(max_length=20, choices=[
        ('pretest', 'Pretest'),
        ('training', 'Training'),
        ('posttest', 'Posttest')
    ])
    condition = models.CharField(max_length=20, choices=[('gamified', 'Gamified'), ('control', 'Control')])
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    score = models.IntegerField(default=0)
    total_time_seconds = models.IntegerField(null=True, blank=True)
    responses = models.JSONField(default=dict)  # e.g., {"item_123": {"answer": "B", "time": 45, "correct": True}}
    items = models.ManyToManyField(RPMItem)
    longest_streak = models.PositiveIntegerField(default=0)
    answered_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-start_time']

    def __str__(self):
        return f"{self.user.username} - {self.session_type} ({self.condition})"


class RPMChoice(models.Model):
    item = models.ForeignKey(RPMItem, on_delete=models.CASCADE, related_name='choices')
    index = models.PositiveSmallIntegerField()  # 0–7
    image = models.ImageField(upload_to='matrices/choices/')

    class Meta:
        unique_together = ('item', 'index')
        ordering = ['index']

    def __str__(self):
        return f"{self.item.item_id} – Choice {self.index}"