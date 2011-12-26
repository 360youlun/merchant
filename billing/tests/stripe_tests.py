from django.test import TestCase
from billing import get_gateway, CreditCard
from billing.gateway import CardNotSupported
from billing.utils.credit_card import Visa


class StripeGatewayTestCase(TestCase):
    def setUp(self):
        self.merchant = get_gateway("stripe")
        self.credit_card = CreditCard(first_name="Test", last_name="User",
                                      month=10, year=2012,
                                      number="4242424242424242",
                                      verification_value="100")

    def testCardSupported(self):
        self.credit_card.number = "5019222222222222"
        self.assertRaises(CardNotSupported,
                          lambda: self.merchant.purchase(1000, self.credit_card))

    def testCardType(self):
        self.credit_card.number = '4242424242424242'
        self.merchant.validate_card(self.credit_card)
        self.assertEquals(self.credit_card.card_type, Visa)

    def testPurchase(self):
        resp = self.merchant.purchase(1, self.credit_card)
        self.assertEquals(resp["status"], "SUCCESS")

    def testStoreMissingCustomer(self):
        self.assertRaises(TypeError,
                          lambda: self.merchant.store())

    def testStoreWithoutBillingAddress(self):
        resp = self.merchant.store(self.credit_card)
        self.assertEquals(resp["status"], "SUCCESS")
        self.assertEquals(resp["response"].active_card.exp_month, self.credit_card.month)
        self.assertEquals(resp["response"].active_card.exp_year, self.credit_card.year)
        self.assertTrue(getattr(resp["response"], "id"))
        self.assertTrue(getattr(resp["response"], "created"))

    def testUnstore(self):
        resp = self.merchant.store(self.credit_card)
        self.assertEquals(resp["status"], "SUCCESS")
        response = self.merchant.unstore(resp["response"].id)
        self.assertEquals(response["status"], "SUCCESS")

    def testRecurring1(self):
        options = {"plan_id": "plaban"}
        resp = self.merchant.recurring(self.credit_card, options=options)
        self.assertEquals(resp["status"], "SUCCESS")
        subscription = resp["response"].subscription
        self.assertEquals(subscription.status, "active")
