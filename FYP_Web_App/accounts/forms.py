from django import forms
from .models import UserDetails

class UserDetailsForm(forms.ModelForm):
    """
        Form used by the user to update their personal information.
    """
    class Meta:
        model = UserDetails
        fields = ['first_name', 'last_name', 'profession', 'university']