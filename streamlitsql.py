import streamlit as st
import pyodbc
import pandas as pd
from io import BytesIO

# Function to establish a database connection
def get_connection(driver, server, database, trusted_connection, username=None, password=None):
    try:
        if trusted_connection:
            conn = pyodbc.connect(
                f"Driver={{{driver}}};"
                f"Server={server};"
                f"Database={database};"
                "Trusted_Connection=yes;"
            )
        else:
            conn = pyodbc.connect(
                f"Driver={{{driver}}};"
                f"Server={server};"
                f"Database={database};"
                f"UID={username};"
                f"PWD={password};"
            )
        return conn
    except Exception as e:
        st.error(f"Unable to connect to SQL Server instance. Error: {e}")
        return None

# Get list of databases
def get_databases(conn):
    query = "SELECT name FROM sys.databases"
    return pd.read_sql(query, conn)['name'].tolist()

# Get list of tables for selected database
def get_tables(conn, database):
    try:
        conn.execute(f"USE {database}")
        query = "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'"
        return pd.read_sql(query, conn)['TABLE_NAME'].tolist()
    except Exception as e:
        st.error(f"Error fetching tables: {e}")
        return []

# Fetch table data with pagination
def get_table_data(conn, database, table_name, start, limit):
    try:
        conn.execute(f"USE {database}")
        query = f"SELECT * FROM {table_name} ORDER BY (SELECT NULL) OFFSET {start} ROWS FETCH NEXT {limit} ROWS ONLY"
        return pd.read_sql(query, conn)
    except Exception as e:
        st.error(f"Error loading table data: {e}")
        return pd.DataFrame()

# Streamlit app
def main():
    # State variable for connection
    if "connection" not in st.session_state:
        st.session_state.connection = None

    # Step 1: Credentials Input Screen
    if st.session_state.connection is None:
        st.title("SQL Server Login")

        # Input fields for credentials
        driver = st.text_input("Driver", value="ODBC Driver 17 for SQL Server")
        server = st.text_input("Server", value="LENOVO-PC\\SQLEXPRESS")
        database = st.text_input("Database", value="master")
        trusted_connection = st.checkbox("Trusted Connection", value=True)
        
        username = password = None
        if not trusted_connection:
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")

        # Button to submit credentials and connect
        if st.button("Test Connection"):
            conn = get_connection(driver, server, database, trusted_connection, username, password)
            if conn:
                st.session_state.connection = conn
                st.success("Connection successful!")

    # Step 2: Main UI (only shown after successful connection)
    if st.session_state.connection:
        conn = st.session_state.connection
        st.title("SQL Server Database Explorer")

        # Load databases and select
        databases = get_databases(conn)
        selected_db = st.selectbox("Select a Database", databases)

        if selected_db:
            # Fetch tables for selected database
            tables = get_tables(conn, selected_db)
            if tables:
                search_term = st.text_input("Search Tables")
                filtered_tables = [table for table in tables if search_term.lower() in table.lower()]

                # Display tables as a list view
                selected_table = st.selectbox("Tables", filtered_tables)
                
                # Load and display table data with pagination
                if selected_table:
                    page_size = 10
                    offset = st.number_input("Page Number", min_value=1, step=1) - 1
                    start = offset * page_size
                    data = get_table_data(conn, selected_db, selected_table, start, page_size)

                    # Display data
                    st.write(f"Displaying data for table: {selected_table}")
                    st.dataframe(data)

                    # Export options
                    if st.button("Export as CSV"):
                        csv = data.to_csv(index=False).encode('utf-8')
                        st.download_button("Download CSV", data=csv, file_name=f"{selected_table}.csv", mime="text/csv")
                    
                    if st.button("Export as Excel"):
                        excel_buffer = BytesIO()
                        with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                            data.to_excel(writer, index=False, sheet_name=selected_table)
                        excel_buffer.seek(0)
                        st.download_button(
                            label="Download Excel",
                            data=excel_buffer,
                            file_name=f"{selected_table}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )

            else:
                st.warning("No tables found in the selected database.")
        
        # Refresh option
        if st.button("Refresh"):
            st.experimental_rerun()

if __name__ == "__main__":
    main()
