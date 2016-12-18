from django import forms
from django.contrib.auth.forms import UserChangeForm

from clubadm.models import User


class SeasonForm(forms.ModelForm):
    def clean(self):
        cleaned_data = super(SeasonForm, self).clean()

        signups_start = cleaned_data.get("signups_start")
        signups_end = cleaned_data.get("signups_end")
        ship_by = cleaned_data.get("ship_by")

        if signups_end <= signups_start:
            self.add_error("signups_end", "Дайте время на регистрацию.")

        if ship_by <= signups_end:
            self.add_error("ship_by", "Дайте время на отправку подарка.")
