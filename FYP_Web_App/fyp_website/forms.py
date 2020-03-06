from django import forms


class RelExInfoForm(forms.Form):
    relation_support_dataset = forms.FileField()
    queries_dataset = forms.FileField()