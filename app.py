import pyodbc
import pandas as pd
import requests
import json
from datetime import datetime, timedelta


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
            "timestamp": pd.to_datetime(row["TimeOfSample"]).isoformat()  # ISO 8601 format
        })

    # Creating the payload
    payload = {
        "measurements": measurements,
        "name": "Sample Parameter",
        "hostDevice": 1001,
        "device": 501,
        "log": 1.0,
        "point": "P1",
        "id_equipment": 42
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    # Sending data to the collect API endpoint
    response = requests.post(url, headers=headers, data=json.dumps(payload))

    if response.status_code == 201:
        print("Data sent successfully.")
    else:
        print(f"Failed to send data. Status code: {response.status_code}, Response: {response.text}")


# Execution of the function for testing
if __name__ == "__main__":
    mdb_file_path = r"C:\Users\Shadow\Desktop\sparksentry-exe\Trendlog_0027400_0000000027-M-2024-03.mdb"
    table_name = "tblTrendlog_0027400_0000000027"
    api_url = "https://api.sparksentry.fr/api/v1/collect/1"
    token = "<your_jwt_token>"

    # Choose mode: "all" for all values or "last24h" for the last 24 hours
    mode = "all"  # or "last24h"

    try:
        data = fetch_values(mdb_file_path, table_name, mode=mode)
        print(data)
        send_data_to_collect_api(data, api_url, token)
    except Exception as e:
        print("Error during data retrieval or sending:", e)

    input("Press Enter to close the program...")