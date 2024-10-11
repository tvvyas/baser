import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date

# Define session state variables
if 'button_clicked' not in st.session_state:
    st.session_state.button_clicked = False

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

def callback():
    st.session_state.button_clicked = True

def login(username, password):
    # Retrieve user credentials from Streamlit app settings
    stored_username = st.secrets["user_credentials"]["username"]
    stored_password = st.secrets["user_credentials"]["password"]
    if username == stored_username and password == stored_password:
        return True
    return False

# Retrieve database credentials from Streamlit app settings
db_name = st.secrets["database"]["name"]
db_username = st.secrets["database"]["username"]
db_password = st.secrets["database"]["password"]

# Connect to SQLite database using credentials
conn = sqlite3.connect(f'{db_name}.db')
c = conn.cursor()

# Create inventory and history tables if they don't exist
c.execute('''CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY,
                name TEXT,
                gst_number TEXT,
                start_date TEXT,
                end_date TEXT,
                quantity INTEGER,
                rate_per_day REAL,
                bill_amount REAL,
                payment_amount REAL DEFAULT 0
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
                timestamp TEXT
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
def log_history(inventory_id, name, gst_number, start_date, end_date, quantity, rate_per_day, bill_amount, payment_amount):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        c.execute('''INSERT INTO history (inventory_id, name, gst_number, start_date, end_date, quantity, rate_per_day, bill_amount, payment_amount, timestamp)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                     (inventory_id, name, gst_number, start_date, end_date, quantity, rate_per_day, bill_amount, payment_amount, timestamp))
        conn.commit()
    except Exception as e:
        st.error(f"Error logging history: {e}")

# Login page
if not st.session_state.logged_in:
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if login(username, password):
            st.session_state.logged_in = True
            st.success("Logged in successfully!")
        else:
            st.error("Invalid username or password")
else:
    # Sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox("Select a page", ["Add Item", "Update Item", "Delete Item", "View Items", "History", "Logout"])

    if page == "Logout":
        st.session_state.logged_in = False
        st.success("Logged out successfully!")
        st.experimental_rerun()

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

            # Calculate bill amount
            bill_amount = calculate_bill(start_date, end_date, rate_per_day, quantity)

            submit_button = st.form_submit_button(label='Add Item')

        if submit_button:
            try:
                c.execute('''INSERT INTO inventory (name, gst_number, start_date, end_date, quantity, rate_per_day, bill_amount, payment_amount)
                             VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', (name, gst_number, start_date, end_date, quantity, rate_per_day, bill_amount, payment_amount))
                conn.commit()
                # Get the id of the last inserted item
                inventory_id = c.lastrowid
                log_history(inventory_id, name, gst_number, start_date, end_date, quantity, rate_per_day, bill_amount, payment_amount)
                st.success("Item added successfully!")
            except Exception as e:
                st.error(f"Error adding item: {e}")

    # Update Item Page
    elif page == "Update Item":
        st.title("Update Inventory Item")
        item_id = st.number_input("Enter the ID of the item to update", min_value=1)

        if (st.button("Load Item", on_click=callback) or st.session_state.button_clicked):
            try:
                c.execute("SELECT * FROM inventory WHERE id=?", (item_id,))
                item = c.fetchone()

                if item:
                    name, gst_number, start_date, end_date, quantity, rate_per_day, bill_amount, payment_amount = item[1], item[2], item[3], item[4], item[5], item[6], item[7], item[8]
                    start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                    end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

                    with st.form(key='update_item_form'):
                        name = st.text_input("Name", value=name)
                        gst_number = st.text_input("GST Number", value=gst_number)
                        start_date = st.date_input("Start Date", value=start_date)
                        end_date = st.date_input("End Date", value=end_date)
                        quantity = st.number_input("Quantity", min_value=0, value=quantity)
                        rate_per_day = st.number_input("Rate per Day", min_value=0.0, value=rate_per_day)
                        payment_amount = st.number_input("Payment Amount", min_value=0.0, value=payment_amount)

                        # Calculate bill amount
                        bill_amount = calculate_bill(start_date, end_date, rate_per_day, quantity)

                        submit_button = st.form_submit_button(label='Update Item')

                        if submit_button:
                            try:
                                c.execute('''UPDATE inventory SET
                                             name=?, gst_number=?, start_date=?, end_date=?, quantity=?, rate_per_day=?, bill_amount=?, payment_amount=?
                                             WHERE id=?''', (name, gst_number, start_date, end_date, quantity, rate_per_day, bill_amount, payment_amount, item_id))
                                conn.commit()
                                log_history(item_id, name, gst_number, start_date, end_date, quantity, rate_per_day, bill_amount, payment_amount)
                                st.success("Item updated successfully!")
                            except Exception as e:
                                st.error(f"Error updating item: {e}")
            except Exception as e:
                st.error(f"Error loading item: {e}")

    # Delete Item Page
    elif page == "Delete Item":
        st.title("Delete Inventory Item")
        item_id = st.number_input("Enter the ID of the item to delete", min_value=1)
        if st.button("Delete Item"):
            try:
                c.execute("SELECT * FROM inventory WHERE id=?", (item_id,))
                item = c.fetchone()
                if item:
                    name, gst_number, start_date, end_date, quantity, rate_per_day, bill_amount, payment_amount = item[1], item[2], item[3], item[4], item[5], item[6], item[7], item[8]
                    c.execute("DELETE FROM inventory WHERE id=?", (item_id,))
                    conn.commit()
                    log_history(item_id, name, gst_number, start_date, end_date, quantity, rate_per_day, bill_amount, payment_amount)
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
