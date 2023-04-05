# Import the necessary libraries
import ipywidgets as widgets
from IPython.display import display, Image
from PIL import Image as PILImage
from hana_ml.dataframe import ConnectionContext
from dotenv import load_dotenv

import openai
import os
openai.organization = os.getenv('OPENAI_ORGANIZATION')
##openai.api_key = os.getenv('0X12AI0Ugfcz51vbMAmnT3BlbkFJnkaU9djkDLJcmutkn7sL')
openai.api_key = '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'

from ipywidgets import Dropdown, VBox
import pyhdb
import pyodbc
import json
import os
import pandas as pd
import re
from sqlalchemy import create_engine

# Create the first dropdown
database_type_dropdown = Dropdown(
    options=['--SELECT--','SAP HANA Cloud', 'Azure SQL'],
    value='--SELECT--',
    description='Select database type:',
    style={'description_width': 'initial', 'font-size': '16px'}
)

database_type_dropdown.layout.width = '500px'
database_type_dropdown.layout.height = '30px'

# Create the second dropdown
table_name_dropdown = Dropdown(
    description='Select table name:',
    style={'description_width': 'initial', 'font-size': '16px'}
)

table_name_dropdown.layout.width = '500px'
table_name_dropdown.layout.height = '30px'

user_prompt = widgets.Text(
    value='',
    placeholder='Type here',
    description='Text Query:',
    style={'description_width': 'initial', 'font-size': '16px'}
)

user_prompt.layout.width = '500px'
user_prompt.layout.height = '30px'

# Define the button widget
button = widgets.Button(
    description='Submit'
)



# Define a function to update the second dropdown based on the first dropdown selection
def on_database_type_change(change):
    global cc
    global conn
    global engine
    if change['type'] == 'change' and change['name'] == 'value':
        if change['new'] == 'SAP HANA Cloud':
            # Connect to the SAP HANA Cloud database
            load_dotenv()

            ###dbHost = os.getenv('DB_HOST')
            dbHost = 'e3bd540b-325a-4e89-8404-1e17a1a6cbb8.hna0.prod-eu10.hanacloud.ondemand.com'
            dbPort = 443
            ##dbUser = os.getenv('DB_USER')
            dbUser = 'GE28572'
            dbPwd = 'ObZEAM4VbZ1!'
            #dbTable = "CUSTOMERS"

            cc = ConnectionContext(dbHost, dbPort, dbUser, dbPwd, encrypt=True, sslValidateCertificate=False)
            engine = create_engine(f'hana://GE28572:ObZEAM4VbZ1!@e3bd540b-325a-4e89-8404-1e17a1a6cbb8.hna0.prod-eu10.hanacloud.ondemand.com:443/')
            # Execute a SQL query to retrieve table names
            cursor = cc.connection.cursor()
            cursor.execute("SELECT table_name FROM tables")
            result = cursor.fetchall()
            table_names = [r[0] for r in result]
        else:
            # Connect to the Azure SQL database
            import pymssql

            server = 'viz1sqlserver1.database.windows.net'
            database = 'viz1sqldb3'
            username = 'rk00829942@viz1sqlserver1'
            password = 'Monday@12345'
            conn = pymssql.connect(server=server, user=username, password=password, database=database)

            # Execute a SQL query to retrieve table names
            cursor = conn.cursor()
            cursor.execute("SELECT TABLE_SCHEMA + '.' + TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE' ORDER BY TABLE_SCHEMA, TABLE_NAME")
            result = cursor.fetchall()
            table_names = [r[0] for r in result]

        # Update the options of the second dropdown
        table_name_dropdown.options = table_names

# Attach the function to the first dropdown's value change event
database_type_dropdown.observe(on_database_type_change)

# Define a function that will be called when the user clicks the button
def on_button_click(b):
    # Retrieve the selected values from the dropdowns and the user text prompt
    dropdown1_value = database_type_dropdown.value
    dropdown2_value = table_name_dropdown.value
    user_prompt_value = user_prompt.value
    
    if dropdown1_value == 'SAP HANA Cloud':
      #df = pd.read_sql("SELECT * FROM " + dropdown2_value + " ", cc.connection)
      df = pd.read_sql("SELECT * FROM " + dropdown2_value + " ", engine)
      
    else:
      
      df = pd.read_sql_query("SELECT * FROM " + dropdown2_value + " ", conn)

    #df=table.collect()
    #df['AGE'] = df['AGE'].astype(str)
    #print (df)
    data_gdp = {}

    for column in df:
      data_gdp[column] = df[column].values.tolist()

    # Print the selected values to the console
    print(f'Selected values: {dropdown1_value}, {dropdown2_value}, {user_prompt_value}')
    #prompt = """Please regard the following table: {} 
    
    #The table name is {} . Write a SQL query to answer the following question : {}""".format(json.dumps(data_gdp), dropdown2_value, user_prompt_value)
    prompt = """Please regard the following table: 
    
    The table name is {} . Write a SQL query to answer the following question : {}""".format(dropdown2_value, user_prompt_value)



# Generate text using the OpenAI API
    request = openai.Completion.create(
      model="text-davinci-003",
      prompt=prompt,
      max_tokens=2000,
      n=1,
      stop=None,
      temperature=0.00
    )

    
    print(request)
    # Get the generated text from the first completion
    generated_text = request.choices[0].text
    generated_text = generated_text.replace("\n", " ")

    # Use regular expressions to extract the SQL query
    #sql_query_match = re.search(r'SELECT\s+.*\s+FROM\s+.*\s+WHERE\s+.*', generated_text, re.DOTALL | re.IGNORECASE)
    #sentence = 'in the table?\n\nSELECT DISTINCT country FROM COUNTRIES_BY_GDP;'
    #query_pattern = r"(?i)select\s+.+\s+from\s+.+;"
    query_pattern =  r"(?i)(?<!\S)SELECT\s+.+\s+FROM\s+.+"
    matches = re.findall(query_pattern, generated_text)
    if matches:
        sql_query = matches[0]
        print(sql_query)
    else:
        print("No SQL query found in the sentence.")
        # If a match was found, extract the SQL query


    #sql_query1 = request.choices[0].text

    print("===> {}: {}".format(user_prompt_value, sql_query))
    if dropdown1_value == 'SAP HANA Cloud':
      df = pd.read_sql(sql_query, engine)
      #print(df.collect())
      print(df)
    else:
      df = pd.read_sql_query(sql_query, conn)
      print(df)

    #return df.collect()

# Attach the on_button_click function to the button widget
button.on_click(on_button_click)

tech_mahindra_logo = PILImage.open("Tech_Mahindra_Logo.png")
new_size = (200, 200)

# Resize the image
resized_logo = tech_mahindra_logo.resize(new_size)

# Display the resized image
resized_logo.show()
#tech_mahindra_logo.show()

from IPython.display import HTML, display

subheader_text = "Rise for a more Equal World  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;  Rise to be Future Ready   &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;  Rise to Create Value"

# Define the header text and style
header_text = "Natural Language Query : Smart way to analyze your data"
header_style = "font-size: 24px; font-weight: bold; text-align: center; padding: 20px; background-color: #f2f2f2;"

subheader_style = "font-size: 18px; font-weight: bold; color: red;"
subheader_html = f"<div style='{subheader_style}'>{subheader_text}</div>"
# Create the HTML header element
header_html = f"<div style='{header_style}'>{header_text}</div>"

header_with_subheader_html = subheader_html   +  header_html 

body_style = "background-image: 'background.jpg';"
body_html = f"<body style='{body_style}'>{subheader_html}{header_html}</body>"

html_code = f"<!DOCTYPE html><html>{body_html}</html>"

#print(html_code)
display(HTML(html_code))
# Display the header in the UI
#display(HTML(header_with_subheader_html))

# Display the UI
VBox([database_type_dropdown, table_name_dropdown, user_prompt, button])