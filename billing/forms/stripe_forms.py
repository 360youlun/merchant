from django import forms
import decimal

class StripeForm(forms.Form):
    # Small value to prevent non-zero values. Might need a relook
    amount = forms.DecimalField(min_value=decimal.Decimal('0.001'))
    credit_card_number = forms.CharField(max_length=16)
    credit_card_cvc = forms.CharField(max_length=4)
    credit_card_expiration_month = forms.CharField(max_length=2)
    credit_card_expiration_year = forms.CharField(max_length=2)
