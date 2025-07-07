#Adding the root directory to the path to import utils module

import sys
import os

# Add the root directory (parent of 'utils') to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))


import pandas as pd
from itertools import product
from utils import neonDB as ndb


df = pd.read_csv('base_calculation_file_mmm.csv')
df['Spend_lower'] = df['Spend_lower'].astype(str).str.replace(',', '').astype(float)
df['Spend_upper'] = df['Spend_upper'].astype(str).str.replace(',', '').astype(float)

#generating the elasticity dataset
channel_arr = [[]]
channels = df['Channel'].unique()



for channel in channels:
    # print (brand)
    s_lower = df[df['Channel']==channel]['Spend_lower'].iloc[0].astype(int)
    s_upper = df[df['Channel']==channel]['Spend_upper'].iloc[0].astype(int)
    m = df[df['Channel']==channel]['m'].iloc[0]
    c = df[df['Channel']==channel]['c'].iloc[0]
    
    for spend in range (s_lower,s_upper,50000):
        sales = spend*m + c
        channel_arr.append([channel,spend,sales])       
    df_pde = pd.DataFrame(channel_arr)
df_pde.rename(columns = {0:'Channel',1:'Spend',2:'Sales'},inplace=True)



#Calculate ROI
df_pde['ROI'] = round(df_pde['Sales']/df_pde['Spend'],2)
df_pde['Sales'] = round(df_pde['Sales'],2)
df_pde.dropna(inplace=True)

#we will pivot this table such that all 3 channel spends are combined with each other(650 X 500 X 320 )
# Create a dictionary which will have the universe of values for each brand
channels = df_pde['Channel'].unique()
dfs = {channel: df_pde[df_pde['Channel'] == channel].reset_index(drop=True) for channel in channels}


# Get row indices for each brand df
channel_rows = [list(range(len(dfs[channel]))) for channel in channels]


# Cartesian product of row indices
all_combinations = list(product(*channel_rows))

i=0
# For each combination of row indices, build a row by horizontally joining brand rows
combined_rows = []
for row_idxs in all_combinations:

    row_parts = [dfs[channel].iloc[[idx]].reset_index(drop=True) for channel, idx in zip(channels, row_idxs)]
    #row_part_1 = dfs['Paid Search'].iloc[[0]] --> Paid Search	278715.0	2464863.79	8.84
    #row_pat_2 = dfs['Paid Social'].iloc[[0]] --> Paid Social	209036.0	1742830.68	8.34
    #row_pat_3 = dfs['Email'].iloc[[0]] -->	       Email	    139357.0	1651651.96	11.85

    combined_row = pd.concat(row_parts, axis=1)
    #combined_row =  Paid Search	278715.0	2464863.79	8.84 Paid Social	209036.0	1742830.68	8.34 Email	139357.0	1651651.96	11.85
    combined_rows.append(combined_row)
    i+=1
    print(i)
    # Combine all rows into the final dataframe
final_df = pd.concat(combined_rows, axis=0).reset_index(drop=True)

# # Optional: Clean up column names
new_cols = []
for channel in channels:
    new_cols.extend([f"{col}_{channel}" for col in dfs[channel].columns])
final_df.columns = new_cols


# Sum Sales and Spend columns
def sum_columns_by_prefix(df, prefix, new_col_name):
    cols = [col for col in df.columns if col.startswith(prefix)]
    df[new_col_name] = df[cols].sum(axis=1)
    return df

# Apply transformations for Spend
final_df = sum_columns_by_prefix(final_df, "Spend_", "Total_Spend")
final_df = sum_columns_by_prefix(final_df, "Sales_", "Total_Sales")

 
# Average ROI
def mean_columns_by_prefix(df, prefix, new_col_name):
    cols = [col for col in df.columns if col.startswith(prefix)]
    df[new_col_name] = round(df[cols].apply(pd.to_numeric, errors='coerce').mean(axis=1),2)
    return df

final_df = mean_columns_by_prefix(final_df, "ROI_", "Avg_ROI")

final_df['Net_ROI'] = round(final_df['Total_Sales']/final_df['Total_Spend'],2)

#Add a negative spend column which we can apply maximization function
final_df['Spend_Negative'] = -final_df['Total_Spend']

# final_df.to_csv('spend_universe.csv', index=False)

#write the data to neondb
try:
    final_df.to_sql('spend_universe', ndb.engine, if_exists='replace', index=False)
    print("Data written to spend_universe successfully")
except Exception as e:
    print(f"An error occurred: {e}")
    ndb.conn.rollback()  # Rollback the transaction
    print("Transaction rolled back")

#######Close cursor and connection pool##########
# Close the cursor and return the connection to the pool
finally:
    ndb.cur.close()
    ndb.connection_pool.putconn(ndb.conn)

# Close all connections in the pool
ndb.connection_pool.closeall()
print("Connection pool closed successfully")