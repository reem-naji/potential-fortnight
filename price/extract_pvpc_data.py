import os
import esios

API_KEY = os.getenv('ESIOS_API_KEY') 
client  = esios.ESIOSClient(token=API_KEY)

handle = client.indicators.get(1013)
df = handle.historical("2014-04-01", "2015-10-31")
print(df.head())

df.to_csv(r'price/pvpc_2014_4_to_2015_10.csv')