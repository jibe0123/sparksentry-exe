import os

import pyodbc
import requests
import json
from datetime import datetime, timedelta

print(pyodbc.drivers())

def fetch_jwt_token(login_url, email, password):
    """
    Fetches a JWT token by logging in with the provided credentials.
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
    """
    # Vérification de l'existence du fichier
    if not os.path.exists(mdb_file_path):
        raise FileNotFoundError(f"Le fichier {mdb_file_path} n'existe pas.")

    # Vérification des pilotes disponibles
    drivers = pyodbc.drivers()
    if "Microsoft Access Driver (*.mdb)" not in drivers and "Microsoft Access Driver (*.mdb, *.accdb)" not in drivers:
        raise RuntimeError("Pilote Access non trouvé. Pilotes disponibles : " + str(drivers))



    conn_str = f"DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={mdb_file_path};"
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    if mode == "all":
        query = f"SELECT TimeOfSample, SampleValue, ValueType, Sequence, Index FROM {table_name}"
        cursor.execute(query)
    elif mode == "last24h":
        query = f"SELECT TOP {num_values} TimeOfSample, SampleValue, ValueType, Sequence, Index FROM {table_name} WHERE TimeOfSample >= ? ORDER BY TimeOfSample DESC"
        last_24h = datetime.now() - timedelta(hours=24)
        cursor.execute(query, last_24h)
    else:
        raise ValueError("Invalid mode. Choose 'all' or 'last24h'.")

    rows = cursor.fetchall()
    data = []
    for row in rows:
        data.append({
            "TimeOfSample": row[0],
            "SampleValue": row[1],
            "ValueType": row[2],
            "Sequence": row[3],
            "Index": row[4]
        })

    conn.close()
    return data

def send_data_to_collect_api(data, url, token):
    measurements = []
    for row in data:
        measurements.append({
            "value": row["SampleValue"],
            "timestamp": row["TimeOfSample"].strftime("%Y-%m-%dT%H:%M:%SZ")
        })

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

    response = requests.post(url, headers=headers, data=json.dumps(payload))

    if response.status_code == 201:
        print("Data sent successfully.")
    else:
        print(f"Failed to send data. Status code: {response.status_code}, Response: {response.text}")

if __name__ == "__main__":
    mdb_file_path = r"C:\Alerton\Compass\2.0\BAULNE\HABMAISO\trendlogdata\Trendlog_0000015_0000000075.mdb"
    table_name = "tblTrendlog_0000015_0000000075"
    collect_url = "https://api.sparksentry.fr/api/v1/collect/1"
    login_url = "https://api.sparksentry.fr/api/v1/login"

    email = "jb@sparksentry.com"
    password = "root"

    token = fetch_jwt_token(login_url, email, password)
    if not token:
        print("Could not retrieve JWT token, exiting...")
        exit(1)

    mode = "all"

    try:
        data = fetch_values(mdb_file_path, table_name, mode=mode)
        if data:
            print("Data retrieved successfully, preparing to send to API...")
            print(data)
            send_data_to_collect_api(data, collect_url, token)
        else:
            print("No data found, skipping API call.")
    except Exception as e:
        print("Error during data retrieval or sending:", e)

    input("Press Enter to close the program...")