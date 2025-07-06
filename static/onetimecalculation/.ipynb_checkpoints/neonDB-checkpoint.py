import os
from psycopg2 import pool
from dotenv import load_dotenv
import pandas as pd
# Get a connection from the pool
# Load .env file
load_dotenv()

# Get the connection string from the environment variable
connection_string = os.getenv('DATABASE_URL')
# Create a connection pool
connection_pool = pool.SimpleConnectionPool(
    1,  # Minimum number of connections in the pool
    10,  # Maximum number of connections in the pool
    connection_string
)
# Check if the pool was created successfully
if connection_pool:
    print("Connection pool created successfully")


# Get a connection from the pool
conn = connection_pool.getconn()
# Create a cursor object
cur = conn.cursor()
# Execute SQL commands to retrieve the current time and version from PostgreSQL
cur.execute('SELECT NOW();')
time = cur.fetchone()[0]
print(time)


cur.execute('SELECT version();')
version = cur.fetchone()[0]
print(version)


cur.execute('select * from public.price_predictor where id = 1')
df = pd.DataFrame(cur.fetchall())
print(df.head())


cur.execute('CREATE OR REPLACE TABLE public.price_universe (select * from )')
print('id 1 committed to db')

# Close the cursor and return the connection to the pool
cur.close()
connection_pool.putconn(conn)
# Close all connections in the pool
connection_pool.closeall()
# Print the results
print('Current time:', time)
print('PostgreSQL version:', version)