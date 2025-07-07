import numpy as np
import pandas as pd
from utils import neonDB as ndb
from sqlalchemy.sql import text
from babel.numbers import format_currency



def run_price_optimizer(upload_file_path, input_file_path):
    """
    Function to process the uploaded file and input file, apply constraints, 
    and return the final reshaped DataFrame (final_long_df).
    """
    # Log the file path for df_init
    print(f"Loading df_init from: {upload_file_path}")

    # Read the uploaded file and input file
    df_init = pd.read_csv(upload_file_path)
    df_input = pd.read_csv(input_file_path)

    # Combine the two files
    df = pd.concat([df_init, df_input], axis=1)

    # Preprocess the data
    df['Stock Available'] = df['Stock Available'].astype(str).str.replace(',', '').astype(float).astype(int)
    df['MOP'] = df['MOP'].astype(str).str.replace('₹', '').str.replace(',', '').astype(float)
    df['NLC'] = df['NLC'].astype(str).str.replace('₹', '').str.replace(',', '').astype(float)
    df['Units (Pred.)'] = pd.to_numeric(df['Units (Pred.)'], errors='coerce').fillna(0)
    df.fillna(0, inplace=True)


    # Calculate the total units from the upload_file
    total_units_from_upload = df['Units (Pred.)'].sum()

    #calculate base numbers, this will be used to compare the output with the optimized numbers
    df_init['Discount'] = df_init['MOP'] - df_init['Test Price']
    df_init['Discount %'] = (df_init['Discount'] / df_init['MOP']) * 100
    df_init['Discount_per_unit'] = df_init['Discount'] / df_init['Units (Pred.)']
    df_init['GP_per_unit'] = df_init['Test Price'] - df_init['NLC']
    df_init['GP'] = df_init['GP_per_unit'] * df_init['Units (Pred.)']
    df_init['GMV'] = df_init['Test Price'] * df_init['Units (Pred.)']
    df_init['GP_%'] = (df_init['GP'] / df_init['GMV']) * 100

  

    ###______________OBJ FUNCTION__________
    if df['Sales Maximization'][0] == 1:
        max_table_col_name = "Total_GMV"
    elif df['Profit Maximization'][0] == 1:
        max_table_col_name = 'Total_GP'
    elif df['Profitability Maximization'][0] == 1:
        max_table_col_name = 'Net_GP_per'
    else:
        obj_function = 'Undefined'

    ######__________CONSTRAINTS____________

    # 1. Sales
    sales_constraint_lower = df['Sales Constraint Min'][0]
    if df['Sales Constraint Max'][0] == 0:
        sales_constraint_upper = (df['Stock Available'] * df['MOP']).sum()
    else:
        sales_constraint_upper = df['Sales Constraint Max'][0]

    # 2. Profit
    profit_constraint_lower = df['Profit Constraint Min'][0]
    if df['Profit Constraint Max'][0] == 0:
        profit_constraint_upper = (df['Stock Available'] * (df['MOP'] - df['NLC'])).sum()
    else:
        profit_constraint_upper = df['Profit Constraint Max'][0]

    # 3. Profitability constraint
    profitability_constraint_lower = df['Profitability Constraint Min'][0]
    if df['Profitability Constraint Max'][0] == 0:
        profitability_constraint_upper = (((df['MOP'] - df['NLC']) * df['Stock Available']) / 
                                          (df['Stock Available'] * df['MOP'])).sum()*100
    else:
        profitability_constraint_upper = df['Profitability Constraint Max'][0]


    # 4. Quantity constraint
    if df['Quantity Constraint Min'][0] == 0:
        quantity_lower_bound = df['Stock Available'] * 0
    else:
        quantity_lower_bound = (df['Stock Available'] * df['Quantity Constraint Min'][0] / 100)

    if df['Quantity Constraint Max'][0] == 0:
        quantity_upper_bound = df['Stock Available'] * 1
    else:
        quantity_upper_bound = (df['Stock Available'] * df['Quantity Constraint Max'][0] / 100)

    	
    # 5. Discount
    discount_lower_bound = df['Discount % Constraint Min']
    if df['Discount % Constraint Max'][0] == 0:
        discount_upper_bound = (df['Stock Available'] / df['Stock Available']) * 100
    else:
        discount_upper_bound = df['Discount % Constraint Max']

    

    # DataFrame to put together all constraints at article level
    article_list = df['Article#'].to_numpy()
    columns = ['Article#', 'Quantity Constraint Max', 'Quantity Constraint Min',
               'Discount % Constraint Min', 'Discount % Constraint Max']
    data = [article_list, quantity_upper_bound.to_numpy(), quantity_lower_bound.to_numpy(),discount_lower_bound.to_numpy(), discount_upper_bound.to_numpy()]
    df_constraints = pd.DataFrame(columns=columns, data=np.array(data).T)


    # Get values from the first row
    max_discount = df_constraints.loc[0, 'Discount % Constraint Max']
    min_discount = df_constraints.loc[0, 'Discount % Constraint Min']

    # Assign to all rows
    df_constraints['Discount % Constraint Max'] = max_discount
    df_constraints['Discount % Constraint Min'] = min_discount

    #quantity constraints for each sku
    bosch_qty_constraint_min = df_constraints['Quantity Constraint Min'][0]
    bosch_qty_constraint_max = df_constraints['Quantity Constraint Max'][0]
    haier_qty_constraint_min = df_constraints['Quantity Constraint Min'][1]
    haier_qty_constraint_max = df_constraints['Quantity Constraint Max'][1]
    ifb_qty_constraint_min = df_constraints['Quantity Constraint Min'][2]
    ifb_qty_constraint_max = df_constraints['Quantity Constraint Max'][2]
    lg_qty_constraint_min = df_constraints['Quantity Constraint Min'][3]
    lg_qty_constraint_max = df_constraints['Quantity Constraint Max'][3]
    samsung_qty_constraint_min = df_constraints['Quantity Constraint Min'][4]
    samsung_qty_constraint_max = df_constraints['Quantity Constraint Max'][4]
    whirlpool_qty_constraint_min = df_constraints['Quantity Constraint Min'][5]
    whirlpool_qty_constraint_max = df_constraints['Quantity Constraint Max'][5]

    #discount constraint for each sku
    bosch_discount_constraint_min = df_constraints['Discount % Constraint Min'][0]
    bosch_discount_constraint_max = df_constraints['Discount % Constraint Max'][0]
    haier_discount_constraint_min = df_constraints['Discount % Constraint Min'][1]
    haier_discount_constraint_max = df_constraints['Discount % Constraint Max'][1]
    ifb_discount_constraint_min = df_constraints['Discount % Constraint Min'][2]
    ifb_discount_constraint_max = df_constraints['Discount % Constraint Max'][2]
    lg_discount_constraint_min = df_constraints['Discount % Constraint Min'][3]
    lg_discount_constraint_max = df_constraints['Discount % Constraint Max'][3]
    samsung_discount_constraint_min = df_constraints['Discount % Constraint Min'][4]
    samsung_discount_constraint_max = df_constraints['Discount % Constraint Max'][4]
    whirlpool_discount_constraint_min = df_constraints['Discount % Constraint Min'][5]
    whirlpool_discount_constraint_max = df_constraints['Discount % Constraint Max'][5]

    # build the SQL query with constraints


    query = text(""" 
                 with constraint_query as
                 (
                 select * from price_universe 
                 where "Total_GMV">= :sales_constraint_lower and "Total_GMV"<= :sales_constraint_upper
                 and "Total_GP">= :profit_constraint_lower and "Total_GP" <= :profit_constraint_upper
                 and ("Total_GP"/"Total_GMV")*100 >= :profitability_constraint_lower and ("Total_GP"/"Total_GMV")*100 <= :profitability_constraint_upper
                 and "Units_Bosch" >= :bosch_qty_constraint_min and "Units_Bosch" <= :bosch_qty_constraint_max
                 and "Units_Haier" >= :haier_qty_constraint_min and "Units_Haier" <= :haier_qty_constraint_max
                 and "Units_IFB" >= :ifb_qty_constraint_min and "Units_IFB" <= :ifb_qty_constraint_max
                 and "Units_LG" >= :lg_qty_constraint_min and "Units_LG" <= :lg_qty_constraint_max
                 and "Units_Samsung" >= :samsung_qty_constraint_min and "Units_Samsung" <= :samsung_qty_constraint_max
                 and "Units_Whirlpool" >= :whirlpool_qty_constraint_min and "Units_Whirlpool" <= :whirlpool_qty_constraint_max
                 and "Discount_%_Bosch" >= :bosch_discount_constraint_min and "Discount_%_Bosch" <= :bosch_discount_constraint_max
                 and "Discount_%_Haier" >= :haier_discount_constraint_min and "Discount_%_Haier" <= :haier_discount_constraint_max
                 and "Discount_%_IFB" >= :ifb_discount_constraint_min and "Discount_%_IFB" <= :ifb_discount_constraint_max
                 and "Discount_%_LG" >= :lg_discount_constraint_min and "Discount_%_LG" <= :lg_discount_constraint_max
                 and "Discount_%_Samsung" >= :samsung_discount_constraint_min and "Discount_%_Samsung" <= :samsung_discount_constraint_max
                 and "Discount_%_Whirlpool" >= :whirlpool_discount_constraint_min and "Discount_%_Whirlpool" <= :whirlpool_discount_constraint_max
                )
                 select * from constraint_query where "{}" = (select max("{}") from constraint_query)
                 """.format(max_table_col_name, max_table_col_name))
    params = {
        'sales_constraint_lower':sales_constraint_lower,
        'sales_constraint_upper':sales_constraint_upper,
        'profit_constraint_lower': profit_constraint_lower,
        'profit_constraint_upper': profit_constraint_upper,
        'profitability_constraint_lower': profitability_constraint_lower,
        'profitability_constraint_upper': profitability_constraint_upper,
        'bosch_qty_constraint_min': bosch_qty_constraint_min,
        'bosch_qty_constraint_max': bosch_qty_constraint_max,
        'haier_qty_constraint_min': haier_qty_constraint_min,
        'haier_qty_constraint_max': haier_qty_constraint_max,
        'ifb_qty_constraint_min': ifb_qty_constraint_min,
        'ifb_qty_constraint_max': ifb_qty_constraint_max,
        'lg_qty_constraint_min': lg_qty_constraint_min,
        'lg_qty_constraint_max': lg_qty_constraint_max,
        'samsung_qty_constraint_min': samsung_qty_constraint_min,
        'samsung_qty_constraint_max': samsung_qty_constraint_max,
        'whirlpool_qty_constraint_min': whirlpool_qty_constraint_min,
        'whirlpool_qty_constraint_max': whirlpool_qty_constraint_max,
        'bosch_discount_constraint_min': bosch_discount_constraint_min,
        'bosch_discount_constraint_max': bosch_discount_constraint_max,
        'haier_discount_constraint_min': haier_discount_constraint_min, 
        'haier_discount_constraint_max': haier_discount_constraint_max,
        'ifb_discount_constraint_min': ifb_discount_constraint_min,
        'ifb_discount_constraint_max': ifb_discount_constraint_max,
        'lg_discount_constraint_min': lg_discount_constraint_min,
        'lg_discount_constraint_max': lg_discount_constraint_max,
        'samsung_discount_constraint_min': samsung_discount_constraint_min,
        'samsung_discount_constraint_max': samsung_discount_constraint_max,
        'whirlpool_discount_constraint_min': whirlpool_discount_constraint_min,
        'whirlpool_discount_constraint_max': whirlpool_discount_constraint_max
    }
    print(query)
    # Execute the query with parameters
    df_universe = pd.read_sql_query(query, con=ndb.engine,params=params)
    print(df_universe.head())
    print("max table col name:",max_table_col_name)
    
    
    # New Constraint: Sum of all quantities sold should be within 50% of total units from upload_file
    df_universe['Total_Units_Sold'] = (
        pd.to_numeric(df_universe['Units_Bosch'], errors='coerce').fillna(0) +
        pd.to_numeric(df_universe['Units_Haier'], errors='coerce').fillna(0) +
        pd.to_numeric(df_universe['Units_IFB'], errors='coerce').fillna(0) +
        pd.to_numeric(df_universe['Units_LG'], errors='coerce').fillna(0) +
        pd.to_numeric(df_universe['Units_Samsung'], errors='coerce').fillna(0) +
        pd.to_numeric(df_universe['Units_Whirlpool'], errors='coerce').fillna(0)
    )

    output_df = df_universe
        

    #########___________Run objective function_________

    # if obj_function == 'Sales Maximization':
    #     output_df = df_universe[df_universe['Total_GMV'] == df_universe['Total_GMV'].max()]
    # elif obj_function == 'Profit Maximization':
    #     output_df = df_universe[df_universe['Total_GP'] == df_universe['Total_GP'].max()]
    # elif obj_function == 'Profitability Maximization':
    #     output_df = df_universe[df_universe['Total_GMV']/df_universe['Total_GP'] == df_universe['Total_GMV']/df_universe['Total_GP'].max()]
    # else:  # Default: maximize sales
    #     output_df = df_universe[df_universe['Total_GMV'] == df_universe['Total_GMV'].max()]

    ##############____________Re-arrange the output frame to showcase on app_______

    # Extract brand names from column prefixes
    brands = [col.split("_")[1] for col in output_df.columns if col.startswith("Article#_")]

    # Columns for each brand
    brand_cols = ['Article#', 'Price', 'Units', 'GP_per_unit', 'GP', 'GMV', 'GP_%']

    # Collect reshaped brand-level rows
    melted_rows = []
    for brand in brands:
        cols = [f"{col}_{brand}" for col in brand_cols]
        sub_df = output_df[cols].copy()
        sub_df.columns = brand_cols  # Rename to generic

        # Add Stock Available, MOP, and NLC from df_init
        sub_df['Stock Available'] = df_init.loc[df_init['Article#'] == brand, 'Stock Available'].values[0]
        sub_df['MOP'] = df_init.loc[df_init['Article#'] == brand, 'MOP'].values[0]
        sub_df['NLC'] = df_init.loc[df_init['Article#'] == brand, 'NLC'].values[0]

        melted_rows.append(sub_df)

    # Concatenate all
    final_long_df = pd.concat(melted_rows, axis=0).reset_index(drop=True)

    # Add calculated columns
    final_long_df['Discount/Unit'] = final_long_df['MOP'] - final_long_df['Price']
    final_long_df['Discount'] = final_long_df['Discount/Unit'] * final_long_df['Units']
    final_long_df['Discount %'] = round((final_long_df['Discount/Unit']) / final_long_df['MOP']*100,2)

    # Ensure numeric data and handle invalid values
    currency_columns = ['MOP', 'NLC', 'Price', 'GP_per_unit', 'GP', 'GMV']
    for col in currency_columns:
        final_long_df[col] = pd.to_numeric(final_long_df[col], errors='coerce').fillna(0)



    # Debugging: Print GMV and GP columns to verify data
    # print("GMV column:", final_long_df['GMV'].head())
    # print("GP column:", final_long_df['GP'].head())

    # Debugging: Check if final_long_df is empty
    if final_long_df.empty:
        print("Warning: final_long_df is empty after applying constraints.")
        total_gmv = "₹0.00"
        total_gp = "₹0.00"
        avg_gp_per = "0.00%"
    else:
        # Ensure GP column is numeric before summing
        final_long_df['GP'] = pd.to_numeric(final_long_df['GP'], errors='coerce').fillna(0)
        final_long_df['GMV'] = pd.to_numeric(final_long_df['GMV'], errors='coerce').fillna(0)

    # Calculate total GMV and GP
    total_gmv_value = final_long_df['GMV'].sum()
    total_gp_value = final_long_df['GP'].sum()

    print(final_long_df['GMV'])

    # Ensure total_gp_value and total_gmv_value are numeric
    total_gmv_value = total_gmv_value if pd.notnull(total_gmv_value) else 0
    total_gp_value = total_gp_value if pd.notnull(total_gp_value) else 0

    # Format Total GMV and Total GP as INR
    total_gmv = format_currency(total_gmv_value, 'INR', locale='en_IN')
    total_gp = format_currency(total_gp_value, 'INR', locale='en_IN')


    total_base_gmv_value = df_init['GMV'].sum()
    print(total_base_gmv_value)
    total_base_gmv = format_currency(total_base_gmv_value, 'INR', locale='en_IN')
    
    total_base_gp_value = df_init['GP'].sum()
    total_base_gp = format_currency(total_base_gp_value, 'INR', locale='en_IN')
    


    # Calculate the average GP% as the mean of the GP_% column
    avg_gp_per_value = (total_gp_value/total_gmv_value)*100
    avg_gp_per = f"{avg_gp_per_value:.2f}%" if pd.notnull(avg_gp_per_value) else "0.00%"

    avg_base_gp_per = (df_init['GP'].sum() / df_init['GMV'].sum()) *100
    avg_base_gp_per = f"{avg_base_gp_per:.2f}%" if pd.notnull(avg_base_gp_per) else "0.00%"

    # Debugging: Print total units from upload_file
    print(f"avg_gp_per: {avg_gp_per}")
    print(f"Total Base GMV: {total_base_gmv}")
    print(f"Total Base GP: {total_base_gp}")


    # Format specified columns as INR
    currency_columns = ['MOP', 'NLC', 'Discount/Unit', 'Discount', 'GP', 'GMV','Price','GP_per_unit']
    for col in currency_columns:
        final_long_df[col] = final_long_df[col].apply(lambda x: format_currency(x, 'INR', locale='en_IN'))

    # Format GP_per_unit as INR and GP, GP_% as percentages
    final_long_df['Discount %'] = final_long_df['Discount %'].apply(lambda x: f"{x:.2f}%")
    final_long_df['GP_%'] = final_long_df['GP_%'].apply(lambda x: f"{x:.2f}%")

    # Optional: reorder columns
    cols_order = ['Article#', 'Stock Available', 'MOP', 'NLC', 'Price', 'Discount/Unit', 'Discount', 'Discount %',
                  'Units', 'GP_per_unit', 'GP', 'GMV', 'GP_%']
    final_long_df = final_long_df[cols_order]

    return final_long_df, total_gmv, total_gp, avg_gp_per ,total_base_gmv, total_base_gp, avg_base_gp_per