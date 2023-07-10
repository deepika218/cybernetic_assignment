
# Cybernetic Assignment

Thi Project is regarding the assignment provided by Cybernetic with 3 lambda function, 2 URL's for client.



## Installation

Install Cybernetic Assignment with pip

```bash
To install the required packages, follow these steps:

1. Clone the repository: `git clone https://github.com/deepika218/cybernetic_assignment.git`
2. Navigate to the project directory: `cd cybernetic_assignment`
3. Create a virtual environment (optional but recommended): `python -m venv venv`
4. Activate the virtual environment:
   - For Windows: `venv\Scripts\activate`
   - For Unix or Linux: `source venv/bin/activate`
5. Install the required packages: `pip install -r requirements.txt`

The necessary packages will be installed in your environment, ensuring that you have all the dependencies needed to run the script successfully.

```


    
## Deployment

To deploy this project run

```bash
  python main.py --secret-key "XXXXX" --access-key "XXXX" --role-arn "arn:aws:iam::XXXXXX:role/XXXXX"
```


## API Reference

#### Get Currency Exchange

```http
  GET --> lambda_url: currency_exchange --> please find the urls in config_data.json file after executing the main.py file
```

#### Get Currency Exchange with yesterday difference

```http
  GET --> lambda_url: currency_exchange_with_difference --> please find the urls in config_data.json file after executing the main.py file
```



## Features

- Light/dark mode toggle
- Live previews
- Fullscreen mode
- Cross platform


## Project Overview

This project consists of three Lambda functions:

1. currency_exchange: This function fetches today's currency exchange data if executed by cron, otherwise it retrieves yesterday's data.

2. currency_exchange_with_difference: This function fetches today's currency exchange data along with the difference from the previous day, indicating whether it has increased or decreased by a certain amount. If executed by cron, it retrieves today's data; otherwise, it fetches yesterday's data.

3. currency_exchange_update_cron: This function updates the currency exchanges in DynamoDB on a daily basis.

In addition to the Lambda functions, there is an important file called main.py. This file performs the following tasks:

- Creates a table in DynamoDB.
- Installs all the dependencies inside each directory of the Lambda functions.
- Creates a zip file for each directory to deploy as a separate function in Lambda.
- Generates a function URL for each Lambda function.
- Applies a public access policy for each URL.
- Creates a CloudWatch rule to execute the cron job daily at 15:00 UTC.

Certain values in the config_data file are configured to access and select the Lambda functions within the current directory.

