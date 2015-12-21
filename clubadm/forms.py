from django import forms
from django.contrib.auth.forms import UserChangeForm


class SeasonForm(forms.ModelForm):
    def clean(self):
        cleaned_data = super(SeasonForm, self).clean()

        signups_start = cleaned_data.get('signups_start')
        signups_end = cleaned_data.get('signups_end')
        ship_by = cleaned_data.get('ship_by')

        if signups_end <= signups_start:
            self.add_error('signups_end', 'Дайте время на регистрацию.')

        if ship_by <= signups_end:
            self.add_error('ship_by', 'Дайте время на отправку подарка.')


class UserForm(UserChangeForm):
    def clean(self):
        cleaned_data = super(UserForm, self).clean()

        # Должны выполняться в конце всех проверок, поэтому не clean_is_active.

        is_active = cleaned_data.get('is_active')

        if is_active == False and self.instance.is_active == True:
            self.instance.profile.send_notification('Ваш аккаунт заблокирован',
                'Для выяснения причин свяжитесь с пользователем @habraadm.')

        if is_active == True and self.instance.is_active == False:
            self.instance.profile.send_notification('Ваш аккаунт разблокирован',
                'Желаем вам счастливого Нового Года и Рождества! :-)')
