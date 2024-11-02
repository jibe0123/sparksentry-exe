import pyodbc
import pandas as pd
import requests
import json
from datetime import datetime, timedelta


def fetch_jwt_token(login_url, email, password):
    """
    Fetches a JWT token by logging in with the provided credentials.

    :param login_url: The API endpoint for login
    :param email: User email
    :param password: User password
    :return: JWT token as a string if successful, otherwise None
    """
    credentials = {"email": email, "password": password}
    response = requests.post(login_url, json=credentials)

    if response.status_code == 200:
        token = response.json().get("data")
        print("Successfully retrieved JWT token.")
        return token
    else:
        print(f"Failed to retrieve token. Status code: {response.status_code}, Response: {response.text}")
        return None

def fetch_values(mdb_file_path, table_name, mode="all", num_values=24):
    """
    Fetches values from the .mdb file based on the specified mode.

    :param mdb_file_path: Path to the .mdb file
    :param table_name: Name of the table in the .mdb file
    :param mode: "all" to fetch all values or "last24h" to fetch the last 24 values
    :param num_values: Number of values to retrieve for the "last24h" mode
    :return: DataFrame containing the retrieved values
    """
    # Connection to the .mdb file
    conn_str = f"DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={mdb_file_path};ExtendedAnsiSQL=1;"
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    # Query for fetching data based on mode
    if mode == "all":
        query = f"""
        SELECT TimeOfSample, SampleValue, ValueType, Sequence, Index
        FROM {table_name}
        """
        cursor.execute(query)
    elif mode == "last24h":
        query = f"""
        SELECT TOP {num_values} TimeOfSample, SampleValue, ValueType, Sequence, Index
        FROM {table_name}
        WHERE TimeOfSample >= ?
        ORDER BY TimeOfSample DESC
        """
        last_24h = datetime.now() - timedelta(hours=24)
        cursor.execute(query, last_24h)
    else:
        raise ValueError("Invalid mode. Choose 'all' or 'last24h'.")

    # Fetch all rows
    rows = cursor.fetchall()
    data = [list(row) for row in rows]

    # Convert results into DataFrame
    df = pd.DataFrame(data, columns=["TimeOfSample", "SampleValue", "ValueType", "Sequence", "Index"])

    # Close the connection
    conn.close()

    return df


def send_data_to_collect_api(data, url, token):
    measurements = []

    # Formatting data to fit the expected structure
    for _, row in data.iterrows():
        measurements.append({
            "value": row["SampleValue"],
            "timestamp": pd.to_datetime(row["TimeOfSample"]).strftime("%Y-%m-%dT%H:%M:%SZ")
        })

    # Creating the payload
    payload = {
        "measurements": measurements,
        "name": "AN-UAA-1 TEMP RETOUR",
        "hostDevice": 15,
        "device": 1601,
        "log": 75,
        "point": "AV5",
        "id_equipment": 42
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    print("Payload prepared for sending:", json.dumps(payload, indent=2))

    # Sending data to the collect API endpoint
    response = requests.post(url, headers=headers, data=json.dumps(payload))

    if response.status_code == 201:
        print("Data sent successfully.")
    else:
        print(f"Failed to send data. Status code: {response.status_code}, Response: {response.text}")


if __name__ == "__main__":
    mdb_file_path = r"C:\Alerton\Compass\2.0\BAULNE\HABMAISO\trendlogdata\Trendlog_0000015_00000000075.mdb"
    table_name = "Trendlog_0000015_00000000075"
    collect_url = "https://api.sparksentry.fr/api/v1/collect/1"
    login_url = "https://api.sparksentry.fr/api/v1/login"

    # Credentials for login
    email = "jb@sparksentry.com"
    password = "root"

    # Retrieve JWT token
    token = fetch_jwt_token(login_url, email, password)
    if not token:
        print("Could not retrieve JWT token, exiting...")
        exit(1)

    # Choose mode: "all" for all values or "last24h" for the last 24 hours
    mode = "all"

    try:
        data = fetch_values(mdb_file_path, table_name, mode=mode)

        # Check if there is any data to send
        if not data.empty:
            print("Data retrieved successfully, preparing to send to API...")
            print(data)
            send_data_to_collect_api(data, collect_url, token)
        else:
            print("No data found, skipping API call.")
    except Exception as e:
        print("Error during data retrieval or sending:", e)

    input("Press Enter to close the program...")