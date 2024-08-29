import streamlit as st
import pandas as pd
import numpy as np
import re

st.set_page_config(layout="wide")
st.title('Sandhills Fleet App')

upload_tab, data_tab = st.tabs(['Upload File', 'Data'])

#### TAB 1: Upload File
data = upload_tab.file_uploader('Upload CSV File', type='csv')

#### FUNCTIONS
def define_date_pattern(pattern_string):
    return r'(\d{1,2}[-./]\d{1,2}[-./]\d{2})\s*(-\s*(' + pattern_string + r')|\s*(' + pattern_string + r')\s*-)(?!.{0,10}FB)'

def define_price_pattern(pattern_string):
    return r'\d{1,2}/\d{1,2}/\d{2}\s*-\s*(' + pattern_string + r')\s*(\d{1,3}(?:,\d{3})*)\s*(?!.{0,10}FB)'

def check_pattern(pattern, string):
    return re.search(pattern, string, re.IGNORECASE)

def load_data(file_path):
    data = pd.read_csv(file_path)
    return pd.DataFrame(data)

def filter_columns(df):
    return df[['StockNumber', 'DisplayOnSite', 'InternalNotes', 'SaleListPrice',]]

def convert_to_datetime(df, column):
    return df[column].apply(lambda x: pd.to_datetime(x, errors='coerce'))

#### TAB 2: Data
with data_tab:
    if data is not None:
        df = load_data(data)
        df = filter_columns(df)
        
        df.rename(columns={'SaleListPrice':'CurrentPrice'}, inplace=True)
        
        # create new columns for the updated pictures, inspection uploaded, and updated price dates
        df['UpdatedPictures'] = None
        df['InspectionUploaded'] = None
        df['UpdatedPriceDate'] = None
        df['UpdatedPriceAmount'] = None
        df['StartingDate'] = None
        df['StartingPrice'] = None
        
        for index, row in df.iterrows():
            if pd.isna(row['InternalNotes']):
                continue
            else:
                row['InternalNotes'] = str(row['InternalNotes'])
                
                pattern_pictures = define_date_pattern('Updated Pictures|Updated Photos|Pictures Verified|Photos Verified')
                pattern_listed = define_date_pattern('Listed|Quick Listed')
                pattern_inspections = define_date_pattern('Inspection Uploaded')
                pattern_price_dates = define_date_pattern('Updated Price')
                pattern_price_amounts = define_price_pattern('Updated Price')
                pattern_starting_date = define_date_pattern('Starting Price')
                pattern_starting_price = define_price_pattern('Starting Price')
                
                match_pictures = check_pattern(pattern_pictures, row['InternalNotes'])
                match_listed = check_pattern(pattern_listed, row['InternalNotes'])
                match_inspections = check_pattern(pattern_inspections, row['InternalNotes'])
                match_price_dates = check_pattern(pattern_price_dates, row['InternalNotes'])
                match_price_amounts = check_pattern(pattern_price_amounts, row['InternalNotes'])
                match_starting_date = check_pattern(pattern_starting_date, row['InternalNotes'])
                match_starting_price = check_pattern(pattern_starting_price, row['InternalNotes'])
                
                if match_pictures:
                    df.at[index, 'UpdatedPictures'] = match_pictures.group(1)
                elif match_listed:
                    df.at[index, 'UpdatedPictures'] = match_listed.group(1)
                if match_inspections:
                    df.at[index, 'InspectionUploaded'] = match_inspections.group(1)
                if match_price_dates:
                    df.at[index, 'UpdatedPriceDate'] = match_price_dates.group(1)
                if match_price_amounts:
                    df.at[index, 'UpdatedPriceAmount'] = match_price_amounts.group(2)
                if match_starting_date:
                    df.at[index, 'StartingDate'] = match_starting_date.group(1)
                if match_starting_price:
                    df.at[index, 'StartingPrice'] = match_starting_price.group(2)
                    
        df['UpdatedPictures'] = convert_to_datetime(df, 'UpdatedPictures')
        df['InspectionUploaded'] = convert_to_datetime(df, 'InspectionUploaded')
        df['UpdatedPriceDate'] = convert_to_datetime(df, 'UpdatedPriceDate')
        df['StartingDate'] = convert_to_datetime(df, 'StartingDate')
        
        # photo aging
        df['PhotoAging'] = (pd.to_datetime('today') - df['UpdatedPictures']).dt.days
        
        # price aging
        df['PriceAging'] = (pd.to_datetime('today') - df['UpdatedPriceDate']).dt.days
        
        df = df[[
            'StockNumber',
            'DisplayOnSite',
            'StartingDate',
            'StartingPrice',
            'UpdatedPriceDate',
            'UpdatedPriceAmount',
            'CurrentPrice',
            'PriceAging',
            'UpdatedPictures',
            'PhotoAging',
            'InspectionUploaded',
        ]]
        
        df = df.sort_values(by=['StartingDate', 'PhotoAging', 'PriceAging'], ascending=[True, False, False])
        
        st.dataframe(df)
        st.download_button('Download Data', df.to_csv(index=False), 'fleet_data.csv', 'text/csv')

