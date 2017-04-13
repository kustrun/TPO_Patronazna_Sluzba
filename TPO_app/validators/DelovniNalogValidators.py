from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from datetime import datetime
from django.forms.formsets import BaseFormSet

def dateGreaterThanToday(value):
    today = datetime.now().date()
    userDate = value

    if userDate < today:
        raise ValidationError(
            _('%(userDate)s je v preteklosti.'),
            params={'userDate': userDate.strftime('%d.%m.%Y')},
        )
