from allauth.account.forms import SignupForm
from django import forms

from accounts.models import Role


ROLE_CHOICES = [
    (Role.COACH, "Trenér"),
    (Role.ATHLETE, "Svěřenec"),
]


class EnduroSignupForm(SignupForm):
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        required=True,
        widget=forms.Select(attrs={"class": "form-select eb-input"}),
    )

    def save(self, request):
        user = super().save(request)
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.save(update_fields=["first_name", "last_name"])
        user.profile.apply_role(self.cleaned_data["role"])
        return user


class GoogleProfileCompletionForm(forms.Form):
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        required=True,
        widget=forms.Select(attrs={"class": "form-select eb-input"}),
    )

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        if user is not None and not self.is_bound:
            self.fields["first_name"].initial = user.first_name
            self.fields["last_name"].initial = user.last_name
            self.fields["role"].initial = getattr(user.profile, "role", Role.ATHLETE)

    def save(self):
        if self.user is None:
            raise ValueError("GoogleProfileCompletionForm.save() requires a user.")

        self.user.first_name = self.cleaned_data["first_name"]
        self.user.last_name = self.cleaned_data["last_name"]
        self.user.save(update_fields=["first_name", "last_name"])
        self.user.profile.apply_role(self.cleaned_data["role"])
        return self.user
