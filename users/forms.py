from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class SimpleRegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=False,
        help_text="Optional – only needed if you want to reset your password later."
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make the labels nicer
        self.fields['username'].help_text = "Required. Letters, digits and @/./+/-/_ only."
        self.fields['password1'].help_text = "Your password must be at least 8 characters."
        self.fields['password2'].help_text = "Enter the same password again for verification."