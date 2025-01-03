import pandas as pd
import requests
import re

# import eter-export-2021-FR.xlsx
df = pd.read_excel('eter-export-2021-IT.xlsx')

# Replace column 'ETER ID' column
df.rename(columns={'ETER ID': 'ETER_ID'}, inplace=True)

# Replace column 'Institution Name' column
df.rename(columns={'Institution Name': 'Name'}, inplace=True)

# Replace column 'Legal status' column
df.rename(columns={'Legal status': 'Category'}, inplace=True)

# Replace column 'Institutional website' column
df.rename(columns={'Institutional website': 'Url'}, inplace=True)

# Replace column 'Institution Category standardized' column
df.rename(columns={'Institution Category standardized': 'Institution_Category_Standardized'}, inplace=True)

# Replace column 'Member of European University alliance' column
df.rename(columns={'Member of European University alliance': 'Member_of_European_University_alliance'}, inplace=True)

# Replace column 'Region of establishment (NUTS 2)' column
df.rename(columns={'Region of establishment (NUTS 2)': 'NUTS2'}, inplace=True)

# Replace column 'Region of establishment (NUTS 3)' column
df.rename(columns={'Region of establishment (NUTS 3)': 'NUTS3'}, inplace=True)

# Replace values ​​in 'category' column
# OBS: government dependent we will assume as public
category_replaces = {0: 'public', 1: 'private', 2: 'public'}
df['Category'] = df['Category'].replace(category_replaces)

# Replace the values ​​in the 'Institution Category standardized' column
institutions_category_replaces = {0: 'Other', 1: 'University', 2: 'University of applied sciences'}
df['Institution_Category_Standardized'] = df['Institution_Category_Standardized'].replace(institutions_category_replaces)

# Replace the value in the 'Member of European University alliance' column
member_of_European_University_alliance_replaces = {0: 'No', 1: 'Yes'}

df['Member_of_European_University_alliance'] = df['Member_of_European_University_alliance'].replace(member_of_European_University_alliance_replaces)

# Remove White spaces
df['Url'] = df['Url'].str.strip()

# Remove the http and https from url
df['Url'] = df['Url'].str.replace(r'^https?://', '', regex=True)

# Remove the third bar from the url
df['Url'] = df['Url'].str.replace(r'/.*', '', regex=True)


# Import NUTS2013-NUTS2016.xlsx and select the right sheet
# Source: https://ec.europa.eu/eurostat/documents/345175/629341/NUTS2013-NUTS2016.xlsx
# Import NUTS2013-NUTS2016.xlsx and select the right sheet
dfNuts16Raw = pd.read_excel('NUTS2013-NUTS2016.xlsx', sheet_name='NUTS2013-NUTS2016', header=1)

dfNuts2_2016 = dfNuts16Raw[['Code 2016', 'NUTS level 2']].copy()
dfNuts2_2016.rename(columns={
    'Code 2016': 'NUTS2',
    'NUTS level 2': 'NUTS2_Label_2016'
}, inplace=True)

# Create NUTS3 mapping DataFrame for 2016
dfNuts3_2016 = dfNuts16Raw[['Code 2016', 'NUTS level 3']].copy()
dfNuts3_2016.rename(columns={
    'Code 2016': 'NUTS3',
    'NUTS level 3': 'NUTS3_Label_2016'
}, inplace=True)

# Merge df with NUTS2 and NUTS3 for 2016
df = pd.merge(df, dfNuts2_2016, on='NUTS2', how='left')
df = pd.merge(df, dfNuts3_2016, on='NUTS3', how='left')

# Import NUTS2021.xlsx
dfNuts21Raw = pd.read_excel('NUTS2021.xlsx', sheet_name='NUTS & SR 2021')

# Create NUTS2 mapping DataFrame for 2021
dfNuts2_2021 = dfNuts21Raw[['Code 2021', 'NUTS level 2']].copy()
dfNuts2_2021.rename(columns={
    'Code 2021': 'NUTS2',
    'NUTS level 2': 'NUTS2_Label_2021'
}, inplace=True)

# Create NUTS3 mapping DataFrame for 2021
dfNuts3_2021 = dfNuts21Raw[['Code 2021', 'NUTS level 3']].copy()
dfNuts3_2021.rename(columns={
    'Code 2021': 'NUTS3',
    'NUTS level 3': 'NUTS3_Label_2021'
}, inplace=True)

# Merge df with NUTS2 and NUTS3 for 2021
df = pd.merge(df, dfNuts2_2021, on='NUTS2', how='left')
df = pd.merge(df, dfNuts3_2021, on='NUTS3', how='left')

# Arrange NUTS related columns in desired order
nuts_columns = [
    'NUTS2', 'NUTS2_Label_2016', 'NUTS2_Label_2021',
    'NUTS3', 'NUTS3_Label_2016', 'NUTS3_Label_2021'
]

# Find columns that already exist in the DataFrame
existing_nuts_columns = [col for col in nuts_columns if col in df.columns]

# Determine the position where NUTS columns should be inserted (after 'Url')
insertion_point = df.columns.get_loc('Url') + 1

# Get remaining columns without duplicating or changing original order
remaining_columns = [col for col in df.columns if col not in existing_nuts_columns]

# Insert NUTS columns in desired position
new_column_order = (
    remaining_columns[:insertion_point]
    + existing_nuts_columns
    + remaining_columns[insertion_point:]
)

# Reorganize DataFrame with new column order
df = df[new_column_order]

# verifiy duplicate url

def check_duplicates_url(df, coluna_url='Url'):    
    def extract_domain_without_www(url):
        try:
            url = re.sub(r'www\.', '', url)
            domain = url.split('/')[0]
            return domain
        except:
            return None

    df['domain_without_www'] = df[coluna_url].apply(extract_domain_without_www)

    duplicateds = df[df.duplicated(subset=['domain_without_www'], keep=False)].dropna(subset=['domain_without_www'])

    if duplicateds.empty:
        print("No duplicate URLs were found (after removing 'www').")
    else:
        print("Duplicate URLs found (after removing 'www'):")
        print(duplicateds[[coluna_url, 'domain_without_www','ETER_ID']])

        domains_duplicateds = duplicateds['domain_without_www'].unique()
        print("\nUnique duplicate domains:\n", domains_duplicateds)

check_duplicates_url(df)

# Sanatize

# Remove IT0032 Università degli Studi di MACERATA
# Because ERR_ADDRESS_UNREACHABLE
df = df[df['ETER_ID'] != 'IT0032']

# Remove IT0178 Conservatorio di PESARO "Gioacchino Rossini"
# Because of expired https
df = df[df['ETER_ID'] != 'IT0178']

# Enrichment

# Change url of IT0162 Conservatorio di GENOVA "Nicolò Paganini"
# Because the url was wrong
df.loc[df['ETER_ID'] == 'IT0162', 'Url'] = 'www.conspaganini.it'

# Change url of IT0203 Conservatorio di GENOVA "Nicolò Paganini"
# Because the url was wrong
df.loc[df['ETER_ID'] == 'IT0203', 'Url'] = 'www.conscremona.it'


# saving data on CSV file
file_name = 'italy-heis.csv'
df.to_csv(file_name, index=False, encoding='utf-8')
