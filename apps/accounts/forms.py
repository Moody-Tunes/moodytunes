from django import forms
from django.core.exceptions import ValidationError

from accounts.models import MoodyUser


def validate_matching_passwords(password, confirm_password):
    """
    Validate that a new password equals the confirmation password
    :return: Two-tuple of field and ValidationError to add to the form errors field
    """
    if password != confirm_password:
        return (
            'password',
            ValidationError('Please double check your entered password matches your confirmation password')
        )

    return None


class UpdateUserInfoForm(forms.Form):
    username = forms.CharField(max_length=150, required=False)
    email = forms.EmailField(required=False)
    confirm_password = forms.CharField(max_length=64, widget=forms.PasswordInput, required=False)
    password = forms.CharField(max_length=64, widget=forms.PasswordInput, required=False)

    def clean_password(self):
        new_password = self.cleaned_data.get('password')
        confirm_password = self.cleaned_data.get('confirm_password')

        if new_password:
            error = validate_matching_passwords(new_password, confirm_password)

            if error:
                self.add_error(*error)

        return new_password


class CreateUserForm(forms.Form):
    username = forms.CharField(max_length=150)
    confirm_password = forms.CharField(max_length=64, widget=forms.PasswordInput)
    password = forms.CharField(max_length=64, widget=forms.PasswordInput)

    def clean_password(self):
        new_password = self.cleaned_data.get('password')
        confirm_password = self.cleaned_data.get('confirm_password')

        validate_matching_passwords(new_password, confirm_password)

        error = validate_matching_passwords(new_password, confirm_password)

        if error:
            self.add_error(*error)

        return new_password

    def clean_username(self):
        username = self.cleaned_data.get('username')

        if MoodyUser.objects.filter(username=username).exists():
            self.add_error(
                'username',
                ValidationError('This username is already taken. Please choose a different one')
            )

        return username
