import os
import unittest
from unittest import mock

from currency_exchange_update_cron.update_currency_exchange_price_daily import currency_exchange_price_daily


class TestUpdateCurrencyExchangePriceDaily(unittest.TestCase):

    @mock.patch("update_currency_exchange_price_daily.requests.get")
    def test_lambda_handler_success(self, mock_get):
        mock_get.return_value.status_code = 200
        # mock_get.return_value.content = b"<?xml version='1.0'?><data>Test Data</data>"
        mock_get.return_value.content = """<?xml version="1.0" encoding="UTF-8"?>
                                            <gesmes:Envelope xmlns:gesmes="http://www.gesmes.org/xml/2002-08-01" xmlns="http://www.ecb.int/vocabulary/2002-08-01/eurofxref">
                                                <gesmes:subject>Reference rates</gesmes:subject>
                                                <gesmes:Sender>
                                                    <gesmes:name>European Central Bank</gesmes:name>
                                                </gesmes:Sender>
                                                <Cube>
                                                    <Cube time='2023-07-06'>
                                                        <Cube currency='USD' rate='1.0899'/>
                                                        <Cube currency='JPY' rate='156.57'/>
                                                        <Cube currency='ZAR' rate='20.6276'/></Cube>
                                                </Cube>
                                            </gesmes:Envelope>"""

        event = {}
        context = {}
        os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
        response = currency_exchange_price_daily(event, context)

        self.assertEqual(response["statusCode"], 200)

    @mock.patch("update_currency_exchange_price_daily.requests.get")
    def test_lambda_handler_failure(self, mock_get):
        mock_get.return_value.status_code = 404

        event = {}
        context = {}

        os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

        response = currency_exchange_price_daily(event, context)

        self.assertEqual(response["statusCode"], 400)
        self.assertEqual(response["body"], "{\"message\": \"Failure\"}")


if __name__ == '__main__':
    unittest.main()
