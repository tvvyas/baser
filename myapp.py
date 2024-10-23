import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date

# Define session state variables
if 'button_clicked' not in st.session_state:
    st.session_state.button_clicked = False

def callback():
    st.session_state.button_clicked = True   


# Retrieve database credentials from Streamlit app settings
db_name = st.secrets["database"]["name"]
db_username = st.secrets["database"]["username"]
db_password = st.secrets["database"]["password"]

# Connect to SQLite database using credentials
conn = sqlite3.connect(f'{db_name}.db')
conn.row_factory = sqlite3.Row  # Use row factory for easier data access

# Create inventory and history tables if they don't exist
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS inventory (
    id INTEGER PRIMARY KEY,
    name TEXT,
    gst_number TEXT,
    start_date TEXT,
    end_date TEXT,
    quantity INTEGER,
    rate_per_day REAL,
    bill_amount REAL,
    payment_amount REAL DEFAULT 0,
    item_name TEXT,
    item_storage_location TEXT,
    item_incoming_date TEXT,
    item_outgoing_date TEXT,
    labour_change TEXT
)''')

c.execute('''CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inventory_id INTEGER,
    name TEXT,
    gst_number TEXT,
    start_date TEXT,
    end_date TEXT,
    quantity INTEGER,
    rate_per_day REAL,
    bill_amount REAL,
    payment_amount REAL,
    timestamp TEXT,
    item_name TEXT,
    item_storage_location TEXT,
    item_incoming_date TEXT,
    item_outgoing_date TEXT,
    labour_change TEXT
)''')
conn.commit()

# Function to calculate bill amount
def calculate_bill(start_date, end_date, rate_per_day, quantity):
    if end_date < start_date:
        st.error("End Date cannot be earlier than Start Date.")
        return 0
    days_stored = (end_date - start_date).days
    return days_stored * rate_per_day * quantity

# Function to log history
def log_history(inventory_id, name, gst_number, start_date, end_date, quantity, rate_per_day, bill_amount, payment_amount, item_name, item_storage_location, item_incoming_date, item_outgoing_date, labour_change):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        # Use named placeholders for clarity and security
        c.execute('''INSERT INTO history (inventory_id, name, gst_number, start_date, end_date, quantity, rate_per_day, bill_amount, payment_amount, timestamp, item_name, item_storage_location, item_incoming_date, item_outgoing_date, labour_change)
                   VALUES (:inventory_id, :name, :gst_number, :start_date, :end_date, :quantity, :rate_per_day, :bill_amount, :payment_amount, :timestamp, :item_name, :item_storage_location, :item_incoming_date, :item_outgoing_date, :labour_change)''',
                   {'inventory_id': inventory_id, 'name': name, 'gst_number': gst_number, 'start_date': start_date, 'end_date': end_date, 'quantity': quantity, 'rate_per_day': rate_per_day, 'bill_amount': bill_amount, 'payment_amount': payment_amount, 'timestamp': timestamp, 'item_name': item_name, 'item_storage_location': item_storage_location, 'item_incoming_date': item_incoming_date, 'item_outgoing_date': item_outgoing_date, 'labour_change': labour_change})
        conn.commit()
    except Exception as e:
        st.error(f"Error logging history: {e}")

# Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.selectbox("Select a page", ["Add Item", "Update Item", "Delete Item", "View Items", "History"])

# Add Item Page
if page == "Add Item":
    st.title("Add Inventory Item")
    with st.form(key='add_item_form'):
        name = st.text_input("Name")
        gst_number = st.text_input("GST Number")
        start_date = st.date_input("Start Date", min_value=date(1900, 1, 1))
        end_date = st.date_input("End Date", min_value=date(1900, 1, 1))
        quantity = st.number_input("Quantity", min_value=0)
        rate_per_day = st.number_input("Rate per Day", min_value=0.0)
        payment_amount = st.number_input("Payment Amount", min_value=0.0)
        item_name = st.text_input("Item Name")
        item_storage_location = st.text_input("Item Storage Location")
        item_incoming_date = st.date_input("Item Incoming Date", min_value=date(1900, 1, 1))
        item_outgoing_date = st.date_input("Item Outgoing Date", min_value=date(1900, 1, 1))
        labour_change = st.text_input("Labour Change")

        # Calculate bill amount
        bill_amount = calculate_bill(start_date, end_date, rate_per_day, quantity)

        submit_button = st.form_submit_button(label='Add Item')

    if submit_button:
        try:
            c.execute('''INSERT INTO inventory (name, gst_number, start_date, end_date, quantity, rate_per_day, bill_amount, payment_amount, item_name, item_storage_location, item_incoming_date, item_outgoing_date, labour_change)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (name, gst_number, start_date, end_date, quantity, rate_per_day, bill_amount, payment_amount, item_name, item_storage_location, item_incoming_date, item_outgoing_date, labour_change))
            conn.commit()
            # Get the id of the last inserted item
            inventory_id = c.lastrowid
            log_history(inventory_id, name, gst_number, start_date, end_date, quantity, rate_per_day, bill_amount, payment_amount, item_name, item_storage_location, item_incoming_date, item_outgoing_date, labour_change)
            st.success("Item added successfully!")
        except Exception as e:
            st.error(f"Error adding item: {e}")

# Update Item Page
elif page == "Update Item":
    st.title("Update Inventory Item")

    # Retrieve customer names from the database
    c.execute("SELECT name FROM inventory")
    customer_names = [row[0] for row in c.fetchall()]

    # Create a dropdown for selecting the customer name
    selected_customer = st.selectbox("Select Customer", customer_names)

    if selected_customer:
        # Fetch the item details based on the selected customer name
        c.execute("SELECT * FROM inventory WHERE name=?", (selected_customer,))
        item = c.fetchone()

        if item:
            name, gst_number, start_date, end_date, quantity, rate_per_day, bill_amount, payment_amount, item_name, item_storage_location, item_incoming_date, item_outgoing_date, labour_change = item[1], item[2], item[3], item[4], item[5], item[6], item[7], item[8], item[9], item[10], item[11], item[12], item[13]
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            item_incoming_date = datetime.strptime(item_incoming_date, '%Y-%m-%d').date()
            item_outgoing_date = datetime.strptime(item_outgoing_date, '%Y-%m-%d').date()

            with st.form(key='update_item_form'):
                name = st.text_input("Name", value=name)
                gst_number = st.text_input("GST Number", value=gst_number)
                start_date = st.date_input("Start Date", value=start_date)
                end_date = st.date_input("End Date", value=end_date)
                quantity = st.number_input("Quantity", min_value=0, value=quantity)
                rate_per_day = st.number_input("Rate per Day", min_value=0.0, value=rate_per_day)
                payment_amount = st.number_input("Payment Amount", min_value=0.0, value=payment_amount)
                item_name = st.text_input("Item Name", value=item_name)
                item_storage_location = st.text_input("Item Storage Location", value=item_storage_location)
                item_incoming_date = st.date_input("Item Incoming Date", value=item_incoming_date)
                item_outgoing_date = st.date_input("Item Outgoing Date", value=item_outgoing_date)
                labour_change = st.text_input("Labour Change", value=labour_change)

                # Calculate bill amount
                bill_amount = calculate_bill(start_date, end_date, rate_per_day, quantity)

                submit_button = st.form_submit_button(label='Update Item')

            if submit_button:
                try:
                    c.execute('''UPDATE inventory SET
                               name=?, gst_number=?, start_date=?, end_date=?, quantity=?, rate_per_day=?, bill_amount=?, payment_amount=?, item_name=?, item_storage_location=?, item_incoming_date=?, item_outgoing_date=?, labour_change=?
                               WHERE name=?''', (name, gst_number, start_date, end_date, quantity, rate_per_day, bill_amount, payment_amount, item_name, item_storage_location, item_incoming_date, item_outgoing_date, labour_change, selected_customer))
                    conn.commit()
                    log_history(item_id, name, gst_number, start_date, end_date, quantity, rate_per_day, bill_amount, payment_amount, item_name, item_storage_location, item_incoming_date, item_outgoing_date, labour_change)
                    st.success("Item updated successfully!")
                except Exception as e:
                    st.error(f"Error updating item: {e}")

# Delete Item Page
elif page == "Delete Item":
    st.title("Delete Inventory Item")
    item_id = st.number_input("Enter the ID of the item to delete", min_value=1)
    if st.button("Delete Item"):
        try:
            c.execute("SELECT * FROM inventory WHERE id=?", (item_id,))
            item = c.fetchone()
            if item:
                name, gst_number, start_date, end_date, quantity, rate_per_day, bill_amount, payment_amount, item_name, item_storage_location, item_incoming_date, item_outgoing_date, labour_change = item[1], item[2], item[3], item[4], item[5], item[6], item[7], item[8], item[9], item[10], item[11], item[12], item[13]
                c.execute("DELETE FROM inventory WHERE id=?", (item_id,))
                conn.commit()
                log_history(item_id, name, gst_number, start_date, end_date, quantity, rate_per_day, bill_amount, payment_amount, item_name, item_storage_location, item_incoming_date, item_outgoing_date, labour_change)
                st.success("Item deleted successfully!")
            else:
                st.error("Item not found.")
        except Exception as e:
            st.error(f"Error deleting item: {e}")

# View Items Page
elif page == "View Items":
    st.title("View Inventory Items")
    try:
        inventory_data = pd.read_sql_query("SELECT * FROM inventory", conn)
        st.dataframe(inventory_data)
    except Exception as e:
        st.error(f"Error fetching items: {e}")

# History Page
elif page == "History":
    st.title("Inventory History")
    try:
        history_data = pd.read_sql_query("SELECT * FROM history", conn)
        st.dataframe(history_data)
    except Exception as e:
        st.error(f"Error fetching history: {e}")

# Close the database connection
conn.close()
