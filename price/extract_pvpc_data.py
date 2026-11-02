import os
import esios

API_KEY = os.getenv('ESIOS_API_KEY') 
client  = esios.ESIOSClient(token=API_KEY)

indicators = {1013: "2.0A", 1014: "2.0DHA"}

for id, tariff in indicators.items():
    handle = client.indicators.get(id)
    df = handle.historical("2014-04-01", "2015-10-31")
    print(df.head())

    df.to_csv(f'price/pvpc_{tariff}_2014_4_to_2015_10.csv')  