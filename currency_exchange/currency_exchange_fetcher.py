import json
import datetime
import boto3
import pytz


def fetch_items_by_date(table, column_name, column_value):
    """
    Fetches items from the DynamoDB table based on a specific date column value.

    Args:
        table (DynamoDB.Table): The DynamoDB table object.
        column_name (str): The name of the column to filter on.
        column_value (str): The value to filter the column on.

    Returns:
        list: A list of items matching the filter criteria.
    """
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
    """
    Lambda function that fetches currency exchange data for a specific date.

    Args:
        event (dict): The event data.
        context (LambdaContext): The context object.

    Returns:
        dict: The response object containing the status code and response body.
    """
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
