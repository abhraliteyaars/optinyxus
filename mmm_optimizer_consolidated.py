import pandas as pd
from babel.numbers import format_currency
from utils import neonDB as ndb
from sqlalchemy.sql import text

def run_mmm_optimizer(base_file_path, input_file_path):
    """
    Function to process the uploaded file and input file, apply constraints, 
    and return the final reshaped DataFrame (final_long_df).
    """

##########---------------Read files---------------------

    #User inputs
    df_input = pd.read_csv(input_file_path)
    df_input.fillna(0,inplace=True)
    
    #base file with test spend data
    df_base = pd.read_csv(base_file_path)
    base_spend = df_base['Test Spend'].sum()
    base_sales = df_base['GMV'].sum()
    base_roi = round(base_sales/base_spend,2)
    print('df_input:',df_input.head())
     

    
    ##########---------------Objective function ---------------------
    
    if (df_input['Sales Maximization'][0] ==1):
        # df_output = df_universe[df_universe['Total_Sales']==df_universe['Total_Sales'].max()]
        max_table_col_name = "Total_Sales"
    elif (df_input['Spend Minimization'][0] ==1):
        # df_output = df_universe[df_universe['Total_Spend']==df_universe['Total_Spend'].min()]
        max_table_col_name = "Spend_Negative"  # Negative spend for minimization
    else:
        # df_output = df_universe[df_universe['Net_ROI']==df_universe['Net_ROI'].max()]
        max_table_col_name = "Net_ROI"

    
    ##########---------------Constraint building---------------------
    
    ###SPEND
    #if user gives no lower spend constraint then we assume minimum spend across channels (spend_lower) else the value provided by user
    if(df_input['Spend Constraint Min'].values[0]==0):
        spend_constraint_min = 0 # A very small number to represent no lower limit
    else:
        spend_constraint_min = df_input['Spend Constraint Min'][0]
  
    

    #if user gives no upper spend constraint then we assume maximum spend across channels (spend_upper) else the value provided by user
    if(df_input['Spend Constraint Max'].values[0]==0):
        spend_constraint_max = 9999999999999999 # A very large number to represent no upper limit
    else:
        spend_constraint_max = df_input['Spend Constraint Max'][0]
    
    
    ###SALES
    #if user gives no lower sales constraint then we assume minimum sales across channels (wrt spend_lower) else the value provided by user
    if(df_input['Sales Constraint Min'].values[0]==0):
        sales_constraint_min = 0 # A very small number to represent no lower limit
    else:
        sales_constraint_min = df_input['Sales Constraint Min'][0]
    
    
    #if user gives no upper sales constraint then we assume maximum sales across channels (wrt spend_upper) else the value provided by user
    if(df_input['Sales Constraint Max'].values[0]==0):
        sales_constraint_max = 99999999999999999 # A very large number to represent no upper limit
    else:
        sales_constraint_max = df_input['Sales Constraint Max'][0]
    
    # #### ROI
    
    #if user gives no ROI min constraint we take the minimum possible ROI which is Sales_min/Spend_max else the value provided by user
    if(df_input['ROI % Constraint Min'].values[0]==0):
        roi_constraint_min = 0 # A very small number to represent no lower limit
    else:
        roi_constraint_min = df_input['ROI % Constraint Min'][0]
    

    
    #if user gives no ROI max constraint then we assume maximum possible which is Sales_max/Spend_min else the value provided by user
    if(df_input['ROI % Constraint Max'].values[0]==0):
        roi_constraint_max = 99999999999999999 # A very large number to represent no upper limit
    else:
        roi_constraint_max = df_input['ROI % Constraint Max'][0]

    
    ##########---------------Query building---------------------
        #read the universe of combinations file
        ### Filter the universe of combination such that it contains data within constraints

    query = text(""" 
                 with constraint_query as (
                 select * from spend_universe 
                 where "Total_Spend" >= :spend_constraint_min and "Total_Spend" <= :spend_constraint_max
                   and "Total_Sales" >= :sales_constraint_min and "Total_Sales" <= :sales_constraint_max
                   and "Net_ROI" >= :roi_constraint_min and "Net_ROI" <= :roi_constraint_max
                 )
                 select * from constraint_query where "{}" = (select max("{}") from constraint_query)
                 """.format(max_table_col_name, max_table_col_name)
                 )
    params = {
        'spend_constraint_min': int(spend_constraint_min),
        'spend_constraint_max': int(spend_constraint_max),
        'sales_constraint_min': int(sales_constraint_min),
        'sales_constraint_max': int(sales_constraint_max),
        'roi_constraint_min': int(roi_constraint_min),
        'roi_constraint_max': int(roi_constraint_max)
    }
    # Execute the query with parameters
    print(sales_constraint_min, sales_constraint_max, spend_constraint_min, spend_constraint_max, roi_constraint_min, roi_constraint_max)   
    df_universe = pd.read_sql_query(query, con=ndb.engine,params=params)
    print(df_universe.head())
    
    ### Filter the universe of combination such that it contains data within constraints
    
    
    # df_universe = df_universe[(df_universe['Total_Spend']>=spend_constraint_min) & (df_universe['Total_Spend']<=spend_constraint_max)]
    # df_universe = df_universe[(df_universe['Total_Sales']>=sales_constraint_min) & (df_universe['Total_Sales']<=sales_constraint_max)]
    # df_universe = df_universe[(df_universe['Net_ROI']>=roi_constraint_min) & (df_universe['Net_ROI']<=roi_constraint_max)]
    
      # to ensure we get the maximum sales in case of multiple row outputs
    df_output =df_universe[df_universe['Total_Sales']==df_universe['Total_Sales'].max()]  

    #convert -ve sales to positive sales
    # df_output['Total_Spend'] = df_output['Spend_Negative'].abs()
    ##############____________Re-arrange the output frame to showcase on app_______
    
    # Extract channel names from column prefixes
    channels = [col.split("_")[1] for col in df_output.columns if col.startswith("Channel_")]
    
    # Columns for each channel
    channel_cols = ['Channel', 'Sales', 'Spend', 'ROI']
    
    # Collect reshaped channel-level rows
    melted_rows = []
    for channel in channels:
        cols = [f"{col}_{channel}" for col in channel_cols]
        sub_df = df_output[cols].copy()
        sub_df.columns = channel_cols  # Rename to generic
    
        melted_rows.append(sub_df)
    
    # Concatenate all
    final_long_df = pd.concat(melted_rows, axis=0).reset_index(drop=True)
    
    #calculate total values
    total_sales = final_long_df['Sales'].sum()
    total_spend = final_long_df['Spend'].sum()
    total_roi =  total_sales / total_spend if total_spend != 0 else None
    
    #format all agg values
    optimized_sales = format_currency(total_sales, 'INR', locale='en_IN')
    optimized_spend = format_currency(total_spend, 'INR', locale='en_IN')
    optimized_roi = f"{total_roi:.2f}%" if pd.notnull(total_roi) else "0.00%"

    #format all base values
    base_sales = format_currency(base_sales, 'INR', locale='en_IN')
    base_spend = format_currency(base_spend, 'INR', locale='en_IN')
    base_roi = f"{base_roi:.2f}%" if pd.notnull(base_roi) else "0.00%"
    
    #format all individual values
    final_long_df['Sales'] = final_long_df['Sales'].apply(lambda x: format_currency(x, 'INR', locale='en_IN'))
    final_long_df['Spend'] = final_long_df['Spend'].apply(lambda x: format_currency(x, 'INR', locale='en_IN'))
    final_long_df['ROI'] = final_long_df['ROI'].apply(lambda x: f"{x:.2f}%" if pd.notnull(x) else "0.00%")
    
    print(final_long_df)
    print("****************************")
    print(df_output)
    return final_long_df,optimized_sales,optimized_spend,optimized_roi,base_sales,base_spend,base_roi

