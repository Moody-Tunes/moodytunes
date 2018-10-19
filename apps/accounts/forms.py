from django import forms
from django.core.exceptions import ValidationError


class UpdateUserInfoForm(forms.Form):
    username = forms.CharField(max_length=150, required=False)
    email = forms.EmailField(required=False)
    confirm_password = forms.CharField(max_length=64, widget=forms.PasswordInput, required=False)
    password = forms.CharField(max_length=64, widget=forms.PasswordInput, required=False)

    def clean_password(self):
        new_password = self.cleaned_data.get('password')
        confirm_password = self.cleaned_data.get('confirm_password')

        if new_password and new_password != confirm_password:
            self.add_error(
                'password',
                ValidationError('Please double check your entered password matches your confirmation password')
            )
