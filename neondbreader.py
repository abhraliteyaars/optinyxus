from utils import neonDB as ndb
import pandas as pd
df = pd.read_csv('static/onetimecalculation/mmm_universe_of_combination_sample.csv')
#write the data to neondb
df.to_sql('market_spend_universe', ndb.engine, if_exists='replace', index=False)
print(df.head())