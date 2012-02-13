# -*- coding: utf-8 -*-
# vim:tabstop=4:expandtab:sw=4:softtabstop=4

import time

from django.test import TestCase
from billing.gateway import CardNotSupported
from billing.utils.credit_card import Visa,CreditCard
from billing import get_gateway
from billing.signals import *

from billing.utils.paylane import *
from billing.models import PaylaneTransaction,PaylaneAuthorization

VALID_TEST_VISA = ''
VALID_TEST_MASTERCARD = '5500000000000004'

class PaylaneTestCase(TestCase):
    def setUp(self):
        self.merchant = get_gateway("paylane")
        self.merchant.test_mode = True
        address = PaylanePaymentCustomerAddress()
        address.street_house = 'Av. 24 de Julho, 1117'
        address.city = 'Lisbon'
        address.zip_code = '1700-000'
        address.country_code = 'PT'
        self.customer = PaylanePaymentCustomer(name='Celso Pinto',email='celso@modelo3.pt',ip_address='8.8.8.8',address=address)
        self.product = PaylanePaymentProduct(description='Paylane test payment')
        
    def tearDown(self):
        pass
        
    def testOneShotPurchaseOK(self):
        credit_card = Visa(first_name='Celso',last_name='Pinto',month=10,year=2012,number='4012888888881881',verification_value=435)
        options = {}
        options['customer'] = self.customer
        options['product'] = self.product
        res = self.merchant.purchase(1.0,credit_card,options=options)
        self.assertEqual(res['status'],'SUCCESS',unicode(res['response']))
        self.assertTrue('transaction' in res['response'])
        self.assertFalse('authorization' in res['response'])
        
    def testRecurringSetupOK(self):
        credit_card = Visa(first_name='Celso',last_name='Pinto',month=10,year=2012,number='4242424242424242',verification_value=435)
        options = {}
        options['customer'] = self.customer
        options['product'] = self.product
        res = self.merchant.recurring(1.0,credit_card,options=options)
        self.assertEqual(res['status'],'SUCCESS',unicode(res['response']))
        self.assertTrue('transaction' in res['response'])
        self.assertTrue('authorization' in res['response'])
        self.assertTrue(res['response']['authorization'].sale_authorization_id > 0)
        
    def testRecurringBillingOK(self):
        time.sleep(60)
        credit_card = Visa(first_name='Celso',last_name='Pinto',month=10,year=2012,number='4111111111111111',verification_value=435)
        options = {}
        options['customer'] = self.customer
        options['product'] = self.product
        res = self.merchant.recurring(1.0,credit_card,options=options)
        self.assertEqual(res['status'],'SUCCESS',unicode(res['response']))
        self.assertTrue('transaction' in res['response'])
        self.assertTrue('authorization' in res['response'])
        
        time.sleep(60)
        res = self.merchant.bill_recurring(12.0,res['response']['authorization'],'OK recurring')
        self.assertEqual(res['status'],'SUCCESS',unicode(res['response']))
        self.assertTrue('transaction' in res['response'])
        self.assertTrue('authorization' in res['response'])

        time.sleep(60)
        res = self.merchant.bill_recurring(12.0,res['response']['authorization'],'OK recurring')
        self.assertEqual(res['status'],'SUCCESS',unicode(res['response']))
        self.assertTrue('transaction' in res['response'])
        self.assertTrue('authorization' in res['response'])

    def testRecurringBillingFailWithChargeback(self):
        time.sleep(60)
        credit_card = Visa(first_name='Celso',last_name='Pinto',month=10,year=2012,number='4111111111111111',verification_value=435)
        options = {}
        options['customer'] = self.customer
        options['product'] = self.product
        res = self.merchant.recurring(1.0,credit_card,options=options)
        self.assertEqual(res['status'],'SUCCESS',unicode(res['response']))
        self.assertTrue('transaction' in res['response'])
        self.assertTrue('authorization' in res['response'])

        time.sleep(60)
        res = self.merchant.bill_recurring(float(PaylaneError.ERR_RESALE_WITH_CHARGEBACK),res['response']['authorization'],'Fail recurring')
        self.assertEqual(res['status'],'FAILURE',unicode(res['response']))
        self.assertTrue('transaction' in res['response'])
        self.assertTrue('error' in res['response'])
        self.assertEqual(res['response']['error'].error_code,PaylaneError.ERR_RESALE_WITH_CHARGEBACK)
