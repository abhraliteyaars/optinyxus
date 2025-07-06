import os
from psycopg2 import pool
from dotenv import load_dotenv
from sqlalchemy import create_engine
import urllib.parse

# Load .env file
load_dotenv()

# Get the connection string from the environment variable
connection_string = os.getenv('DATABASE_URL')

# Parse the connection string
uri = urllib.parse.urlparse(connection_string)

# Extract the endpoint ID from the hostname
endpoint_id = uri.hostname.split('.')[0]

# Add the endpoint ID to the options parameter
if '?' in connection_string:
    connection_string += f'&options=endpoint%3D{endpoint_id}'
else:
    connection_string += f'?options=endpoint%3D{endpoint_id}'

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

# Create SQLAlchemy engine
engine = create_engine(f'postgresql+psycopg2://{connection_string.split("://")[1]}')

##########Limit the script till here##########

# # Execute SQL commands to retrieve the current time and version from PostgreSQL
# cur.execute('SELECT NOW();')
# time = cur.fetchone()[0]

# cur.execute('SELECT version();')
# version = cur.fetchone()[0]

# # Close the cursor and return the connection to the pool
# cur.close()
# connection_pool.putconn(conn)

# # Close all connections in the pool
# connection_pool.closeall()

# # Print the results
# print('Current time:', time)
# print('PostgreSQL version:', version)