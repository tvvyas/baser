import streamlit as st
import pandas as pd
from datetime import datetime

# Initialize or load the inventory data
if 'inventory_data' not in st.session_state:
    st.session_state['inventory_data'] = pd.DataFrame(columns=['Name', 'GST Number', 'Start Date', 'End Date', 'Quantity', 'Rate per Day', 'Bill Amount'])

# Function to calculate bill amount
def calculate_bill(start_date, end_date, rate_per_day):
    days_stored = (end_date - start_date).days
    return days_stored * rate_per_day

# Title of the app
st.title("Baser Cold Storage System")

# Form to add or update inventory items
with st.form(key='inventory_form'):
    name = st.text_input("Name")
    gst_number = st.text_input("GST Number")
    start_date = st.date_input("Start Date")
    end_date = st.date_input("End Date")
    quantity = st.number_input("Quantity", min_value=0)
    rate_per_day = st.number_input("Rate per Day", min_value=0.0)
    
    # Calculate bill amount
    if start_date and end_date:
        bill_amount = calculate_bill(start_date, end_date, rate_per_day)
    else:
        bill_amount = 0
    
    submit_button = st.form_submit_button(label='Add/Update Item')

# Add or update the inventory item
if submit_button:
    new_item = pd.DataFrame([{
        'Name': name,
        'GST Number': gst_number,
        'Start Date': start_date,
        'End Date': end_date,
        'Quantity': quantity,
        'Rate per Day': rate_per_day,
        'Bill Amount': bill_amount
    }])
    
    # Check if the item already exists
    existing_item_index = st.session_state['inventory_data'][st.session_state['inventory_data']['Name'] == name].index
    if not existing_item_index.empty:
        st.session_state['inventory_data'].loc[existing_item_index] = new_item.iloc[0]
        st.success("Item updated successfully!")
    else:
        st.session_state['inventory_data'] = pd.concat([st.session_state['inventory_data'], new_item], ignore_index=True)
        st.success("Item added successfully!")

# Display the inventory data
st.subheader("Inventory Data")
st.dataframe(st.session_state['inventory_data'])

# Option to delete an item
delete_name = st.text_input("Enter the Name of the item to delete")
if st.button("Delete Item"):
    st.session_state['inventory_data'] = st.session_state['inventory_data'][st.session_state['inventory_data']['Name'] != delete_name]
    st.success("Item deleted successfully!")
