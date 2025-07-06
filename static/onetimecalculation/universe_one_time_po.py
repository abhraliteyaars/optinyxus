#Adding the root directory to the path to import utils module
import sys
import os

# Add the root directory (parent of 'utils') to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))


import pandas as pd
from utils import neonDB as ndb
from itertools import product

df=pd.read_csv('base_calculation_file_po.csv')
#generating the elasticity dataset
brand_arr = [[]]
brands = df['Article#'].unique()
for brand in brands:
    # print (brand)
    mop = df[df['Article#']==brand]['MOP'].iloc[0].astype(int)
    nlc = df[df['Article#']==brand]['NLC'].iloc[0].astype(int)
    m = df[df['Article#']==brand]['m'].iloc[0]
    c = df[df['Article#']==brand]['c'].iloc[0]
    # brand_arr.append(brand)
    for price in range (nlc,mop,500):
        quantity = price*m + c
        brand_arr.append([brand,price,quantity])       
    df_pde = pd.DataFrame(brand_arr)
df_pde.rename(columns = {0:'Article#',1:'Price',2:'Units'},inplace=True)
df_pde.dropna(inplace=True)


df = df[['Article#','MOP','NLC']]

df_elasticity = df.merge(df_pde, on = 'Article#')
df_elasticity['Units'] = df_elasticity['Units'].astype(int)



#create calculated columns
df_elasticity['Discount'] = df_elasticity['MOP']-df_elasticity['Price']
df_elasticity['Discount_%'] = round(100*((df_elasticity['MOP']-df_elasticity['Price'])/df_elasticity['MOP']),2)
df_elasticity['Discount_Per_Unit'] = round(df_elasticity['Discount']/df_elasticity['Units'],2)
df_elasticity['GP_per_unit'] = df_elasticity['Price'] - df_elasticity['NLC']
df_elasticity['GP'] = df_elasticity['GP_per_unit'] * df_elasticity['Units']
df_elasticity['GMV'] = df_elasticity['Price'] * df_elasticity['Units']
df_elasticity['GP_%'] = round(100*(df_elasticity['GP']/df_elasticity['GMV']),2)


# Separate into DataFrames per brand
brands = df_elasticity['Article#'].unique()
dfs = {brand: df_elasticity[df_elasticity['Article#'] == brand].reset_index(drop=True) for brand in brands}

# Get row indices for each brand
brand_rows = [list(range(len(dfs[brand]))) for brand in brands]

# Cartesian product of row indices
all_combinations = list(product(*brand_rows))

# For each combination of row indices, build a row by horizontally joining brand rows
combined_rows = []
for row_idxs in all_combinations:
    row_parts = [dfs[brand].iloc[[idx]].reset_index(drop=True) for brand, idx in zip(brands, row_idxs)]
    combined_row = pd.concat(row_parts, axis=1)
    combined_rows.append(combined_row)

# Combine all rows into the final dataframe
final_df = pd.concat(combined_rows, axis=0).reset_index(drop=True)

# Optional: Clean up column names
new_cols = []
for brand in brands:
    new_cols.extend([f"{col}_{brand}" for col in dfs[brand].columns])
final_df.columns = new_cols

# Sum GMV and GP columns
def sum_columns_by_prefix(df, prefix, new_col_name):
    cols = [col for col in df.columns if col.startswith(prefix)]
    df[new_col_name] = df[cols].sum(axis=1)
    return df

# Average GP_per columns
def mean_columns_by_prefix(df, prefix, new_col_name):
    cols = [col for col in df.columns if col.startswith(prefix)]
    df[new_col_name] = df[cols].apply(pd.to_numeric, errors='coerce').mean(axis=1)
    return df

# Apply transformations
final_df = sum_columns_by_prefix(final_df, "GMV_", "Total_GMV")
final_df = sum_columns_by_prefix(final_df, "GP_", "Total_GP")
final_df = mean_columns_by_prefix(final_df, "GP_%", "Avg_GP_per")

print(final_df.shape)
# final_df.to_csv('universe_of_combination.csv',index=False)

#write the data to neondb
final_df.to_sql('price_universe', ndb.engine, if_exists='replace', index=False)


#######Close cursor and connection pool##########
# Close the cursor and return the connection to the pool
ndb.cur.close()
ndb.connection_pool.putconn(ndb.conn)

# Close all connections in the pool
ndb.connection_pool.closeall()
print("Connection pool closed successfully")
