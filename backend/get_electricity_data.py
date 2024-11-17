import requests
import os 
from dotenv import load_dotenv
import pandas as pd
load_dotenv()

def return_avg_electricity():
    url = "https://api.eia.gov/v2/electricity/retail-sales/data?&api_key=" + os.getenv("EIA_API") +"&frequency=monthly&data[0]=price&start=2024-08&sort[0][column]=period&sort[0][direction]=desc&offset=0&length=5000"
    header1 = {"X-Params": {
    "frequency": "monthly",
    "data": [
        "price"
    ],
    "facets": {},
    "start": "2024-08",
    "end": "null",
    "sort": [
        {
            "column": "period",
            "direction": "desc"
        }
    ],
    "offset": 0,
    "length": 5000
    }}
    response1 = requests.get(url)
    if response1.status_code < 400:
        
        df = pd.DataFrame(response1.json()['response']['data'])
        df.dropna()
        df = df[df['sectorName'].str.contains("residential")]
        df = df[['stateid', 'price']]
        return df
    else:
        raise Exception("Cannot retrieve avg electricty data. status code: " + response1.status_code)
# df = return_avg_electricity()

# word = "CA"

# print(float(df.loc[df["stateid"] == word]['price'].values[0]))
    