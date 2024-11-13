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
        st.error(f"Unable to connect to the SQL Server instance. Error: {e}")
        return None

# Function to get a list of databases
def get_databases(conn):
    query = "SELECT name FROM sys.databases"
    return pd.read_sql(query, conn)['name'].tolist()

# Function to get list of tables for selected database
def get_tables(conn, database):
    try:
        conn.execute(f"USE {database}")
        query = "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'"
        return pd.read_sql(query, conn)['TABLE_NAME'].tolist()
    except Exception as e:
        st.error(f"Error fetching tables: {e}")
        return []

# Function to fetch table data with pagination
def get_table_data(conn, database, table_name, start, limit):
    try:
        conn.execute(f"USE {database}")
        query = f"SELECT * FROM {table_name} ORDER BY (SELECT NULL) OFFSET {start} ROWS FETCH NEXT {limit} ROWS ONLY"
        return pd.read_sql(query, conn)
    except Exception as e:
        st.error(f"Error loading table data: {e}")
        return pd.DataFrame()

# Sidebar Navigation
tab = st.sidebar.radio("Navigation", ["Option 1: Choose Server", "Option 2", "Option 3", "Option 4", "Option 5"])

# Server selection options with images
server_options = {
    "Azure SQL": "https://swimburger.net/media/ppnn3pcl/azure.png",
    "MongoDB": "https://devopsdozen.com/wp-content/uploads/2015/08/MongoDB-logo-770x330-01.png",
    "MySQL": "https://pngimg.com/uploads/mysql/mysql_PNG22.png",
    "PostgreSQL": "https://www.kindpng.com/picc/m/394-3944547_postgresql-logo-png-transparent-png.png",
    "SQL Server": "https://e7.pngegg.com/pngimages/515/909/png-clipart-microsoft-sql-server-computer-servers-database-microsoft-microsoft-sql-server-server-computer.png"
}

# Option 1: Choose Server
if tab == "Option 1: Choose Server":
    st.title("Step 1: Choose a Server")
    
    # Server selection dropdown
    selected_server = st.selectbox("Select a Server", options=list(server_options.keys()))
    st.image(server_options[selected_server], width=100)

    # Save the selected server in session state
    st.session_state["selected_server"] = selected_server
    
    # Database connection credentials input
    st.header(f"Enter Credentials for {selected_server}")
    driver = st.text_input("Driver", value="ODBC Driver 17 for SQL Server")
    server = st.text_input("Server")
    database = st.text_input("Database")
    trusted_connection = st.checkbox("Trusted Connection", value=True)
    
    username = password = None
    if not trusted_connection:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

    # Test connection
    if st.button("Connect"):
        conn = get_connection(driver, server, database, trusted_connection, username, password)
        if conn:
            st.session_state["connection"] = conn
            st.success("Connection successful!")
        else:
            st.error("Failed to connect. Please check your credentials.")

    # Display available databases, tables, and data export options after connection
    if "connection" in st.session_state and st.session_state["connection"]:
        conn = st.session_state["connection"]

        # Step 2: Database and Table Selection
        st.subheader("Database Explorer")

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

# Placeholder for Options 2, 3, 4, and 5
elif tab == "Option 2":
    st.title("Option 2")
    st.write("This is a placeholder for additional functionality.")

elif tab == "Option 3":
    st.title("Option 3")
    st.write("This is a placeholder for additional functionality.")

elif tab == "Option 4":
    st.title("Option 4")
    st.write("This is a placeholder for additional functionality.")

elif tab == "Option 5":
    st.title("Option 5")
    st.write("This is a placeholder for additional functionality.")
