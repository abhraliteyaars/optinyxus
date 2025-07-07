from utils import neonDB as ndb
import pandas as pd
df = pd.read_csv('static/onetimecalculation/universe_of_combination_price.csv')
#write the data to neondb
df.to_sql('price_universe', ndb.engine, if_exists='replace', index=False)
print(df.head())