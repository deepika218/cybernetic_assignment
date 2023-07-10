import json
import datetime
import boto3
import pytz
import unittest
from unittest.mock import MagicMock


def fetch_items_by_date(table, column_name, column_value):
    response = table.scan(
        FilterExpression='#column = :value',
        ExpressionAttributeNames={
            '#column': column_name
        },
        ExpressionAttributeValues={
            ':value': column_value
        }
    )
    items = response['Items']
    return items


def fetch_currency_exchange_data(event, context):
    print("Fetching currency exchange data...")
    current_utc_time = datetime.datetime.now(pytz.utc)
    current_hour = current_utc_time.hour
    print("Current UTC Time:", current_utc_time)
    print("Current Hour:", current_hour)
    if current_utc_time.weekday() == 0:
        if current_hour < 15:
            date = current_utc_time - datetime.timedelta(days=3)
        else:
            date = datetime.datetime.now(pytz.utc)
    elif current_hour >= 15:
        date = datetime.datetime.now(pytz.utc)
    else:
        date = current_utc_time - datetime.timedelta(days=1)
    date_val = str(date.date())
    print("Selected Date:", date_val)

    dynamodb = boto3.resource('dynamodb')
    table_name = 'CurrencyExchange'
    table = dynamodb.Table(table_name)
    print("Table Name:", table_name)

    items = fetch_items_by_date(table, column_name='date', column_value=date_val)
    print("Fetched Items:")
    for item in items:
        item['rate'] = float(str(item['rate']))
        print(item)

    body = {
        'data': items,
        'message': 'Data Fetched Successfully',
    }

    print("Response Body:", body)

    return {'statusCode': 200, 'body': json.dumps(body)}


class TestCurrencyExchangeData(unittest.TestCase):
    def test_fetch_currency_exchange_data(self):
        table_mock = MagicMock()
        table_mock.scan.return_value = {
            'Items': [
                {'date': '2022-01-01', 'rate': '1.2'},
                {'date': '2022-01-02', 'rate': '1.3'},
            ]
        }
        dynamodb_mock = MagicMock()
        dynamodb_mock.Table.return_value = table_mock
        boto3.resource = MagicMock(return_value=dynamodb_mock)

        result = fetch_currency_exchange_data({}, {})

        expected_body = {
            'data': [
                {'date': '2022-01-01', 'rate': 1.2},
                {'date': '2022-01-02', 'rate': 1.3},
            ],
            'message': 'Data Fetched Successfully',
        }
        expected_response = {'statusCode': 200, 'body': json.dumps(expected_body)}

        self.assertEqual(result, expected_response)


if __name__ == '__main__':
    unittest.main()
