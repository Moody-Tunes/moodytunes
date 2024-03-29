from hmac import compare_digest

from django import forms
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError

from accounts.models import MoodyUser, UserEmotion


def validate_matching_passwords(password, confirm_password):
    """
    Validate that a new password equals the confirmation password

    :return: Two-tuple of field and ValidationError to add to the form errors field if passwords do not match
    """
    if not compare_digest(password, confirm_password):
        return (
            'password',
            ValidationError('Please double check your entered password matches your confirmation password')
        )

    return None


class BaseUserForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        required=True,
        validators=[UnicodeUsernameValidator()],
        widget=forms.TextInput(attrs={'autofocus': 'autofocus'})
    )
    email = forms.EmailField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Optional'}))
    password = forms.CharField(max_length=64, widget=forms.PasswordInput, required=True)
    confirm_password = forms.CharField(max_length=64, widget=forms.PasswordInput, required=True)

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password', '')

        if new_password:
            # Call settings.AUTH_PASSWORD_VALIDATORS on supplied password
            validate_password(new_password)

            error = validate_matching_passwords(new_password, confirm_password)

            if error:
                self.add_error(*error)

    def clean_username(self):
        username = self.cleaned_data.get('username')

        if MoodyUser.objects.filter(username=username).exists():
            self.add_error(
                'username',
                ValidationError('This username is already taken. Please choose a different one')
            )

        return username


class CreateUserForm(BaseUserForm):
    pass


class UpdateUserForm(BaseUserForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')

        super().__init__(*args, **kwargs)

        # Remove ability to change password in form
        del self.fields['password']
        del self.fields['confirm_password']

    def clean_username(self):
        # If user is updating their username, need to check if it's already taken
        username = self.cleaned_data.get('username')

        if username != self.user.username:
            return super().clean_username()

        return username


class UpdateUserEmotionAttributesForm(forms.ModelForm):
    class Meta:
        model = UserEmotion
        fields = ('energy', 'valence', 'danceability')
