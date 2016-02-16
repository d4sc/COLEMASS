from django.forms import ModelForm
from .models import RecurringChore

class RecurringChoreForm(ModelForm):
    class Meta:
        model = RecurringChore
        fields = ['name', 'active']
        error_messages = {
            'name': {
                'required': "Please enter a chore name.",
            },
        }