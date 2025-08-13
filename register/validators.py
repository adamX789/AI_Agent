from django.contrib.auth.password_validation import MinimumLengthValidator as BaseMinimumLengthValidator
from django.core.exceptions import ValidationError

class MinimumLengthValidator(BaseMinimumLengthValidator):
    def validate(self, password, user=None):
        if len(password) < self.min_length:
            raise ValidationError(
                'Heslo je příliš krátké. Musí obsahovat alespoň %(min_length)d znaků.',
                code='password_too_short',
                params={'min_length': self.min_length},
            )