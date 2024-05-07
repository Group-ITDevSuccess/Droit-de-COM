from datetime import date
from django.core.exceptions import ValidationError
from django import forms

from app.models import Societe
from utils import write_log

societes = [('', '---')]
societes.extend(
    [(society.uid, society.name) for society in Societe.objects.filter(active__exact=True)])


class SearchForm(forms.Form):
    societe = forms.ChoiceField(
        label="Société",
        required=True,
        choices=societes,
        widget=forms.Select(
            attrs={'class': 'mr-sm-2 selectpicker show-tick', 'data-live-search': "true", 'data-width': "auto",
                   'data-style': "btn-primary", "data-size": 10})
    )
    target = forms.ChoiceField(
        widget=forms.Select(attrs={'class': 'selectpicker'}),
        choices=[(year, str(year)) for year in range(date.today().year, 2019, -1)],
        required=True,
        label="Date antérieure",
    )

    def clean(self):
        cleaned_data = super().clean()
        societe = cleaned_data.get('societe')
        target = cleaned_data.get('target')

        if not societe or not target:
            raise ValidationError("Les champs Société et Date antérieure sont obligatoires.")

        return cleaned_data
