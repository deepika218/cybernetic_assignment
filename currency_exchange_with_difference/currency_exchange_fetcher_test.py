import unittest
from unittest.mock import MagicMock
from datetime import datetime, timedelta

import boto3

from currency_exchange_with_difference.currency_exchange_fetcher import fetch_currency_exchange_data
from pytz import utc
import json


class TestFetchCurrencyExchangeData(unittest.TestCase):
    def test_fetch_currency_exchange_data(self):
        # Mock the DynamoDB table
        table_mock = MagicMock()
        table_mock.scan.return_value = {
            'Items': [
                {'currency': 'USD', 'date': '2022-01-01', 'rate': '1.2'},
                {'currency': 'EUR', 'date': '2022-01-01', 'rate': '0.9'},
                {'currency': 'USD', 'date': '2022-01-02', 'rate': '1.3'},
                {'currency': 'EUR', 'date': '2022-01-02', 'rate': '0.8'},
            ]
        }

        # Mock the DynamoDB resource
        dynamodb_mock = MagicMock()
        dynamodb_mock.Table.return_value = table_mock
        boto3.resource = MagicMock(return_value=dynamodb_mock)

        # Set the current UTC time to a specific date and time
        current_utc_time = datetime(2022, 1, 3, 10, 0, 0, tzinfo=utc)

        # Call the Lambda function
        result = fetch_currency_exchange_data({}, {'utc_time': current_utc_time})

        # Expected response body
        expected_body = {
            'data': [
                {'currency': 'USD', 'date': '2022-01-02', 'rate': 1.3, 'yesterday_difference': 0.1},
                {'currency': 'EUR', 'date': '2022-01-02', 'rate': 0.8, 'yesterday_difference': -0.1},
            ],
            'message': 'Data Fetched Successfully',
        }

        # Expected response
        expected_response = {'statusCode': 200, 'body': json.dumps(expected_body)}

        # Set self.maxDiff to None to view the full diff
        self.maxDiff = None


if __name__ == '__main__':
    unittest.main()
