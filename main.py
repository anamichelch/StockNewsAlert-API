from dotenv import load_dotenv
import requests
import datetime as dt
from bs4 import BeautifulSoup
import os
from twilio.rest import Client

load_dotenv("/.env")

STOCK = "TSLA"
COMPANY_NAME = "Tesla"
stock_api_key = os.getenv("stock_api_key")
news_api_key = os.getenv("news_api_key")

## Dates ##
today = dt.date.today()
yesterday = dt.date.fromordinal(dt.date.today().toordinal() - 1)
before_yesterday = dt.date.fromordinal(dt.date.today().toordinal() - 2)
print(yesterday)

## Get Stock Info ##
stock_api_params = {
    "function": "TIME_SERIES_DAILY",
    "symbol": STOCK,
    "outputsize": "compact",
    "apikey": stock_api_key,
}

url = "https://www.alphavantage.co/query"
r = requests.get(url, params=stock_api_params)
stock_data = r.json()


is_over_5 = False
# if yesterday not in stock_data["Time Series (Daily)"]:
#    print("no today info yet")
# else:
today_open = stock_data["Time Series (Daily)"][f"{today}"]["1. open"]
yesterday_close = stock_data["Time Series (Daily)"][f"{yesterday}"]["4. close"]
before_yesterday_close = stock_data["Time Series (Daily)"][f"{before_yesterday}"]["4. close"]
delta = round((float(yesterday_close) / float(before_yesterday_close) - 1)*100,1)

if delta > 5:
    is_over_5 = True
    emoji = "🔺"

elif delta < -5:
    is_over_5 = True
    emoji = "🔻"
else:
    is_over_5 = False

## STEP 2: Use https://newsapi.org
# Instead of printing ("Get News"), actually get the first 3 news pieces for the COMPANY_NAME.
## Get News Info ##
url = ('https://newsapi.org/v2/everything?'
       f'q={COMPANY_NAME}&'
       f'from={today}&'
       'sortBy=popularity&'
       f'apiKey={news_api_key}')

response = requests.get(url)
news_data = response.json()

news_content = []
for i in range(0, 3):
    new_content = (news_data["articles"][i]["description"])
    soup = BeautifulSoup(new_content, features="html.parser")
    news_content.append(soup.get_text())



## STEP 3: Use https://www.twilio.com
# Send a seperate message with the percentage change and each article's title and description to your phone number. 

account_sid = os.getenv("twilio_account_sid")
auth_token = os.getenv("twilio_auth_token")
twilio_phone_number = os.getenv("twilio_phone_number")
my_phone_number = os.getenv("my_phone_number")
client = Client(account_sid, auth_token)

if is_over_5:
    message = client.messages.create(
        body=f'{emoji}{delta}, Briefs: {news_content}',
        from_=f'{twilio_phone_number}',
        to=f'{my_phone_number}'
    )
else:
    print("no news")

# Optional: Format the SMS message like this:
"""
TSLA: 🔺2%
Headline: Were Hedge Funds Right About Piling Into Tesla Inc. (TSLA)?. 
Brief: We at Insider Monkey have gone over 821 13F filings that hedge funds and prominent investors are required to file by the SEC The 13F filings show the funds' and investors' portfolio positions as of March 31st, near the height of the coronavirus market crash.
or
"TSLA: 🔻5%
Headline: Were Hedge Funds Right About Piling Into Tesla Inc. (TSLA)?. 
Brief: We at Insider Monkey have gone over 821 13F filings that hedge funds and prominent investors are required to file by the SEC The 13F filings show the funds' and investors' portfolio positions as of March 31st, near the height of the coronavirus market crash.
"""
