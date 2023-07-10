import decimal
import json
import requests
import xmltodict
import boto3
import uuid


def render_xml_as_dict(url):
    """
    Fetches XML data from the provided URL and converts it to a dictionary.

    Args:
        url (str): The URL to fetch the XML data from.

    Returns:
        dict: The XML data as a dictionary.
    """
    response = requests.get(url)
    if response.status_code == 200:
        xml_data = response.content
        xml_dict = xmltodict.parse(xml_data)
        return xml_dict
    else:
        return {}


def check_existing_key(table, date_val, currency_val):
    """
    Checks if a record with the given date and currency already exists in the DynamoDB table.

    Args:
        table (boto3.resources.factory.dynamodb.Table): The DynamoDB table to check.
        date_val (str): The date value.
        currency_val (str): The currency value.

    Returns:
        bool: True if a matching record exists, False otherwise.
    """
    response = table.scan(
        FilterExpression='#date = :date_val AND #currency = :currency_val',
        ExpressionAttributeNames={
            '#date': 'date',
            '#currency': 'currency'
        },
        ExpressionAttributeValues={
            ':date_val': date_val,
            ':currency_val': currency_val
        }
    )
    return len(response['Items']) > 0


def currency_exchange_price_daily(event, context):
    """
    AWS Lambda handler function to update currency exchange prices daily.
    """
    print("Fetching XML data...")
    url = "http://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml"
    xml_dict = render_xml_as_dict(url)
    print("XML Data:", xml_dict)

    if xml_dict:
        envelope = xml_dict.get('gesmes:Envelope', {})
        cube = envelope.get('Cube', {}).get('Cube', [])
        date_val = cube.get('@time')
        final_val = cube.get('Cube', [])
        items = []
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('CurrencyExchange')
        print("Date:", date_val)

        for i in final_val:
            currency = i.get('@currency')
            is_key_exists = check_existing_key(table=table, date_val=date_val, currency_val=currency)
            print("Currency:", currency)
            print("Key Exists:", is_key_exists)

            if not is_key_exists:
                uuid_val = str(uuid.uuid4())
                item = {
                    'id': uuid_val,
                    'currency': currency,
                    'rate': decimal.Decimal(i.get('@rate')),
                    'date': date_val
                }
                items.append(item)
                print("Item to Insert:", item)

        if items:
            with table.batch_writer() as batch:
                for item in items:
                    batch.put_item(Item=item)
            status_code = 200
            body = 'Data inserted into DynamoDB'
        else:
            body = 'No new data to insert'
            status_code = 200
        print("Response Body:", body)
    else:
        body = {"message": "Failure"}
        status_code = 400
        print("Failure message")

    response = {"statusCode": status_code, "body": json.dumps(body)}
    return response
