import json
import os
import subprocess
import zipfile
import argparse
import boto3
from botocore.exceptions import ClientError

# Step 1: Parse command line arguments
parser = argparse.ArgumentParser()
parser.add_argument('--secret-key', help='AWS secret key')
parser.add_argument('--access-key', help='AWS access key')
parser.add_argument('--role-arn', help='IAM role ARN')
parser.add_argument('--region', help='AWS region')
args = parser.parse_args()


# Step 2: Set AWS credentials from command line arguments
aws_access_key_id = args.access_key
aws_secret_access_key = args.secret_key
role_arn = args.role_arn
aws_region = args.region  # Replace with your desired region

# Step 3: Set the current directory
current_directory = os.getcwd()

# Step 4: Read the JSON configuration file
json_file_path = "config_data.json"


def read_json(file_path):
    with open(file_path, 'r') as json_file:
        data = json.load(json_file)
    return data


json_data = read_json(json_file_path)


# Step 5: Zip Function Directories

def install_dependencies(directory_path):
    # Change to the directory
    os.chdir(directory_path)

    # Check if the requirements.txt file exists
    requirements_file = os.path.join(directory_path, "requirements.txt")
    if os.path.isfile(requirements_file):
        # Install dependencies using pip
        subprocess.check_call(["pip3", "install", "-r", requirements_file, "--target", directory_path])

    # Change back to the original directory
    os.chdir("..")


def zip_directory(directory_path):
    # Get the directory name from the path
    directory_name = os.path.basename(directory_path)
    # Create a zip file with the directory name outside the directory
    zip_filename = f"{directory_name}.zip"

    # Install dependencies in the directory
    install_dependencies(directory_path)

    # Create a ZipFile object with write mode
    with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
        # Add the files to the zip file
        for root, _, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                relative_file_path = os.path.relpath(file_path, directory_path)
                zipf.write(file_path, arcname=relative_file_path)

    print(f"Successfully created zipped file: {zip_filename}")


lambda_paths = json_data.get('lambda_function', {}).keys()
functions_data = json_data.get('lambda_function')

lambda_function_directories = [os.path.join(current_directory, item) for item in lambda_paths]

# Iterate over all subdirectories in the current directory
for item_path in lambda_function_directories:
    if os.path.isdir(item_path):
        zip_directory(item_path)

# Step 6: Create DynamoDB Table

# Create a DynamoDB client
dynamodb_client = boto3.client(
    'dynamodb',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name=aws_region
)

# Set the details for the DynamoDB table
table_name = 'CurrencyExchange'
partition_key = 'id'

# Check if the DynamoDB table already exists
try:
    dynamodb_client.describe_table(TableName=table_name)
    table_exists = True
except dynamodb_client.exceptions.ResourceNotFoundException:
    table_exists = False

if not table_exists:
    # Create the DynamoDB table
    response = dynamodb_client.create_table(
        TableName=table_name,
        AttributeDefinitions=[
            {
                'AttributeName': 'id',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'date',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'currency',
                'AttributeType': 'S'
            }
        ],
        KeySchema=[
            {
                'AttributeName': 'id',
                'KeyType': 'HASH'
            }
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 5,
            'WriteCapacityUnits': 5
        },
        GlobalSecondaryIndexes=[
            {
                'IndexName': 'CurrencyDateIndex',
                'KeySchema': [
                    {
                        'AttributeName': 'currency',
                        'KeyType': 'HASH'
                    },
                    {
                        'AttributeName': 'date',
                        'KeyType': 'RANGE'
                    }
                ],
                'Projection': {
                    'ProjectionType': 'ALL'
                },
                'ProvisionedThroughput': {
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            }
        ]
    )

    # Print the response
    print('DynamoDB table created:', response['TableDescription']['TableArn'])
else:
    print('DynamoDB table already exists:', table_name)

# Step 7: Create or Update Lambda Functions

# Create a Lambda client
lambda_client = boto3.client(
    'lambda',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name=aws_region
)


def create_or_update_lambda_function(func_name, zip_file_path, handler):
    # Check if the Lambda function exists
    try:
        lambda_client.get_function(FunctionName=func_name)
        function_exists = True
    except lambda_client.exceptions.ResourceNotFoundException:
        function_exists = False

    if function_exists:
        # Update the existing Lambda function
        update_response = lambda_client.update_function_code(
            FunctionName=func_name,
            ZipFile=open(zip_file_path, 'rb').read()
        )
        return update_response
    else:
        # Create a new Lambda function
        create_response = lambda_client.create_function(
            FunctionName=func_name,
            Runtime='python3.8',
            Role=role_arn,
            Handler=handler,
            Timeout=10,
            Code={
                'ZipFile': open(zip_file_path, 'rb').read()
            },
        )
        return create_response


def get_lambda_function_url(func_name):
    final_response = {}
    try:
        response = lambda_client.get_function_url_config(FunctionName=func_name)
        # Function URL configuration exists, update it
        response = lambda_client.update_function_url_config(
            FunctionName=func_name,
            AuthType='NONE',
            InvokeMode='BUFFERED'
        )
    except lambda_client.exceptions.ResourceNotFoundException:
        # Function URL configuration does not exist, create it
        response = lambda_client.create_function_url_config(
            FunctionName=func_name,
            AuthType='NONE',
            InvokeMode='BUFFERED'
        )
    final_response["FunctionUrl"] = response.get('FunctionUrl')
    final_response["FunctionArn"] = response.get('FunctionArn')
    statement_id = 'FunctionURLAllowPublicAccess'
    add_permission = True
    try:
        response = lambda_client.get_policy(FunctionName=func_name)
        if 'Policy' in response:
            policy = json.loads(response['Policy'])
            existing_statements = policy.get('Statement', [])
            existing_statement_ids = [statement.get('Sid') for statement in existing_statements]

            if statement_id in existing_statement_ids:
                add_permission = False
    except Exception as e:
        pass

    if add_permission:
        permission_response = lambda_client.add_permission(
            FunctionName=func_name,
            StatementId=statement_id,
            Action='lambda:invokeFunctionUrl',
            Principal='*',
            FunctionUrlAuthType='NONE'
        )
        final_response["policy_config"] = permission_response
    return final_response


urls_data = {}
arn_data = {}

# Iterate over the functions_data dictionary and create or update Lambda functions
for func_name, val in functions_data.items():
    zip_file = f"{func_name}.zip"
    function_arn = create_or_update_lambda_function(func_name, zip_file, val)
    function_url = get_lambda_function_url(func_name)
    urls_data[func_name] = function_url.get("FunctionUrl")
    arn_data[func_name] = function_url.get("FunctionArn")

for key, val in urls_data.items():
    print(f"Function Name: {key}, URL: {val}")

for key, val in arn_data.items():
    print(f"Function Name: {key}, URL: {val}")


def update_json_file(json_file_path, key_to_update, new_value):
    # Read the JSON file and load its contents into a dictionary
    with open(json_file_path, 'r') as json_file:
        data = json.load(json_file)

    # Update the value of the specified key
    data[key_to_update] = new_value

    # Write the updated dictionary back to the JSON file
    with open(json_file_path, 'w') as json_file:
        json.dump(data, json_file, indent=4)


json_file_path = 'config_data.json'
key_to_update = 'lambda_arn'
new_value = arn_data

update_json_file(json_file_path, key_to_update, new_value)

key_to_update = 'lambda_url'
new_value = urls_data
update_json_file(json_file_path, key_to_update, new_value)

# Step 8: Create or Update CloudWatch Event Rules

cloudwatch_client = boto3.client('events', aws_access_key_id=aws_access_key_id,
                                 aws_secret_access_key=aws_secret_access_key,
                                 region_name=aws_region)


def create_or_update_cloudwatch_event_rule(rule_name, rule_description, schedule_expression, target_lambda_arn):
    try:
        response = cloudwatch_client.put_rule(
            Name=rule_name,
            ScheduleExpression=schedule_expression,
            State='ENABLED',
            Description=rule_description,
        )
        print(f"CloudWatch Event Rule '{rule_name}' created successfully.")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceAlreadyExistsException':
            # Rule already exists, update it
            response = cloudwatch_client.put_rule(
                Name=rule_name,
                ScheduleExpression=schedule_expression,
                State='ENABLED',
                Description=rule_description,
            )
            print(f"CloudWatch Event Rule '{rule_name}' updated successfully.")
        else:
            # Other error occurred, handle as needed
            print("Error occurred while creating/updating CloudWatch Event Rule:", str(e))

    # Add the target to the rule
    response = cloudwatch_client.put_targets(
        Rule=rule_name,
        Targets=[
            {
                'Id': '1',
                'Arn': target_lambda_arn
            }
        ]
    )

    # Print the response
    print(response)


cloud_watch_rule_cron_func = json_data.get('cloud_watch_rule_cron')
lambda_arn = json_data.get('lambda_arn')

for func_name, cron_expr in cloud_watch_rule_cron_func.items():
    rule_name = func_name + "_cron"
    rule_description = f'{func_name} description'
    schedule_expression = cron_expr
    target_lambda_arn = lambda_arn.get(func_name)

    create_or_update_cloudwatch_event_rule(rule_name, rule_description, schedule_expression, target_lambda_arn)
