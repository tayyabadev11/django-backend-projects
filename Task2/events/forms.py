from django import forms

class RegistrationForm(forms.Form):
    name = forms.CharField(max_length=100)
    phone = forms.CharField(max_length=20, required=False)
    tickets = forms.IntegerField(min_value=1, max_value=5, initial=1)
