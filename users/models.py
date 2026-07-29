from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Profile(models.Model):
    CONDITION_CHOICES = [
        ('control', 'Control (Non-gamified)'),
        ('gamified', 'Intervention (Gamified)'),
    ]

    PROGRESS_CHOICES = [
        ('registered', 'Just registered'),
        ('questionnaire1', 'Questionnaire 1 done'),
        ('pretest', 'Pretest done'),
        ('training1', 'First training done'),
        ('posttest1', 'Post-test 1 done'),
        ('questionnaire2', 'Questionnaire 2 done'),
        ('instruction', 'Instruction page seen'),
        ('free_use', 'Free use period'),
        ('posttest2', 'Post-test 2 done'),
        ('questionnaire3', 'Questionnaire 3 done'),
        ('finished', 'Study finished'),
    ]

    # Study progress
    progress = models.CharField(
        max_length=20,
        choices=[
            ('registered', 'Just registered'),
            ('questionnaire1', 'Questionnaire 1 done'),
            ('pretest', 'Pretest done'),
            ('training1', 'First training done'),
            ('posttest1', 'Post-test 1 done'),
            ('questionnaire2', 'Questionnaire 2 done'),
            ('instruction', 'Instruction page seen'),
            ('free_use', 'Free use period'),
            ('posttest2', 'Post-test 2 done'),
            ('questionnaire3', 'Questionnaire 3 done'),
            ('finished', 'Study finished'),
        ],
        default='registered'
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='control')

    # Study progress
    progress = models.CharField(max_length=20, choices=PROGRESS_CHOICES, default='registered')

    # Daily streak fields (already added earlier)
    current_daily_streak = models.PositiveIntegerField(default=0)
    longest_daily_streak = models.PositiveIntegerField(default=0)
    last_activity_date = models.DateField(null=True, blank=True)

    # Last login
    last_login_at = models.DateTimeField(null=True, blank=True)

    free_use_started = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} – {self.get_condition_display()} – {self.progress}"


class QuestionnaireResponse(models.Model):
    QUESTIONNAIRE_CHOICES = [
        ('q1', 'Questionnaire 1 (Background)'),
        ('q2', 'Questionnaire 2'),
        ('q3', 'Questionnaire 3'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='questionnaire_responses')
    questionnaire = models.CharField(max_length=5, choices=QUESTIONNAIRE_CHOICES)
    answers = models.JSONField(default=dict)         
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'questionnaire')   # one response per questionnaire per user
        ordering = ['questionnaire']

    def __str__(self):
        return f"{self.user.username} – {self.get_questionnaire_display()}"


# Automatically create a profile when a new user is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()