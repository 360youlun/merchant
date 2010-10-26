from billing import Gateway
from paypal.pro.helpers import PayPalWPP
from paypal.pro.exceptions import PayPalFailure
from billing.utils.credit_card import Visa, MasterCard, AmericanExpress, Discover
from billing.signals import *

class PayPalGateway(Gateway):
    default_currency = "USD"
    supported_countries = ["US"]
    supported_cardtypes = [Visa, MasterCard, AmericanExpress, Discover]
    homepage_url = "https://merchant.paypal.com/us/cgi-bin/?&cmd=_render-content&content_ID=merchant/wp_pro"
    display_name = "PayPal Website Payments Pro"

    def __init__(self):
        pass
    
    def purchase(self, money, credit_card, options={}):
        """Using PAYPAL DoDirectPayment, charge the given
        credit card for specified money"""
        if not self.validate_card(credit_card):
            raise InvalidCard("Invalid Card")

        params = {}
        params['creditcardtype'] = credit_card.card_type.card_name
        params['acct'] = credit_card.number
        params['expdate'] = '%02d%04d' % (credit_card.month, credit_card.year)
        params['cvv2'] = credit_card.verification_value
        params['ipaddress'] = options['request'].META.get("REMOTE_ADDR", "")
        params['amt'] = money

        if options.get("email"):
            params['email'] = options["email"]
        
        address = options.get("billing_address", {})
        first_name = None
        last_name = None
        try:
            first_name, last_name = address.get("name", "").split(" ")
        except ValueError:
            pass
        params['firstname'] = first_name or credit_card.first_name
        params['lastname'] = last_name or credit_card.last_name
        params['street'] = address.get("address1", '')
        params['street2'] = address.get("address2", "")
        params['city'] = address.get("city", '')
        params['state'] = address.get("state", '')
        params['countrycode'] = address.get("country", '')
        params['zip'] = address.get("zip", '')
        params['phone'] = address.get("phone", "")

        shipping_address = options.get("shipping_address", None)
        if shipping_address:
            params['shiptoname'] = shipping_address["name"]
            params['shiptostreet'] = shipping_address["address1"]
            params['shiptostreet2'] = shipping_address.get("address2", "")
            params['shiptocity'] = shipping_address["city"]
            params['shiptostate'] = shipping_address["state"]
            params['shiptocountry'] = shipping_address["country"]
            params['shiptozip'] = shipping_address["zip"]
            params['shiptophonenum'] = shipping_address.get("phone", "")
        
        wpp = PayPalWPP(options['request']) 
        try:
            response = wpp.doDirectPayment(params)
            transaction_was_successful.send(sender=self,
                                            type="purchase",
                                            response=response)
        except PayPalFailure, e:
            transaction_was_unsuccessful.send(sender=self,
                                              type="purchase",
                                              response=e)
            # Slight skewness because of the way django-paypal
            # is implemented.
            return {"status": "FAILURE", "response": e}
        return {"status": response.ack.upper(), "response": response}

    def authorize(self, money, credit_card, options = {}):
        if not self.validate_card(credit_card):
            raise InvalidCard("Invalid Card")
        raise NotImplementedError

    def capture(self, money, authorization, options = {}):
        raise NotImplementedError

    def void(self, identification, options = {}):
        raise NotImplementedError

    def credit(self, money, identification, options = {}):
        raise NotImplementedError

    def recurring(self, money, creditcard, options = {}):
        raise NotImplementedError

    def store(self, creditcard, options = {}):
        raise NotImplementedError

    def unstore(self, identification, options = {}):
        raise NotImplementedError
