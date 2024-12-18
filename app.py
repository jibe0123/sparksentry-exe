import os

import pyodbc
import requests
from datetime import datetime, timedelta

parameters = [
    {
        "id_parameter": 2,
        "name": "VFD_RETURN_MODULATION",
        "hostDevice": 2013009,
        "device": 2013000,
        "log": 12,
        "point": "AO-1",
        "id_equipment": 3,
        "unit": "%",
        "mdb_path": r"C:\Alerton\Compass\2.0\BAULNE\HILLPARK\TrendlogData\Trendlog_2013000_0000000012.mdb",
        "table_name": "tblTrendlog_2013000_0000000012"
    },
    {
        "id_parameter": 3,
        "name": "VFD_SUPPLY_MODULATION",
        "hostDevice": 2013009,
        "device": 2013000,
        "log": 20,
        "point": "AO-0",
        "id_equipment": 3,
        "unit": "%",
        "mdb_path": r"C:\Alerton\Compass\2.0\BAULNE\HILLPARK\TrendlogData\Trendlog_2013000_0000000020.mdb",
        "table_name": "tblTrendlog_2013000_0000000020"
    },
    {
        "id_parameter": 4,
        "name": "RETURN_TEMPERATURE",
        "hostDevice": 2013009,
        "device": 2013000,
        "log": 28,
        "point": "AV-2",
        "id_equipment": 3,
        "unit": "°C",
        "mdb_path": r"C:\Alerton\Compass\2.0\BAULNE\HILLPARK\TrendlogData\Trendlog_2013000_0000000028.mdb",
        "table_name": "tblTrendlog_2013000_0000000028"
    },
    {
        "id_parameter": 5,
        "name": "SUPPLY_TEMPERATURE_AFTER_REHEAT",
        "hostDevice": 2013009,
        "device": 2013000,
        "log": 26,
        "point": "AV-3",
        "id_equipment": 3,
        "unit": "°C",
        "mdb_path": r"C:\Alerton\Compass\2.0\BAULNE\HILLPARK\TrendlogData\Trendlog_2013000_0000000026.mdb",
        "table_name": "tblTrendlog_2013000_0000000026"
    },
    {
        "id_parameter": 6,
        "name": "OUTSIDE_TEMPERATURE",
        "hostDevice": 2013020,
        "device": 2013000,
        "log": 4,
        "point": "AV-800",
        "id_equipment": 3,
        "unit": "°C",
        "mdb_path": r"C:\Alerton\Compass\2.0\BAULNE\HILLPARK\TrendlogData\Trendlog_2013000_0000000004.mdb",
        "table_name": "tblTrendlog_2013000_0000000004"
    }
]

def fetch_jwt_token(login_url, email, password):
    credentials = {"email": email, "password": password}
    response = requests.post(login_url, json=credentials)
    if response.status_code == 200:
        print("Successfully retrieved JWT token.")
        return response.json().get("data")
    else:
        raise Exception(f"Failed to retrieve token: {response.status_code}, {response.text}")

def fetch_values(mdb_file_path, table_name, mode="last48h"):
    if not os.path.exists(mdb_file_path):
        raise FileNotFoundError(f"File {mdb_file_path} does not exist.")
    conn_str = f"DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={mdb_file_path};"
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    if mode == "last48h":
        query = f"SELECT TimeOfSample, SampleValue FROM {table_name} WHERE TimeOfSample >= ? ORDER BY TimeOfSample DESC"
        last_48h = datetime.now() - timedelta(hours=48)
        cursor.execute(query, last_48h)
    else:
        query = f"SELECT TimeOfSample, SampleValue FROM {table_name}"
        cursor.execute(query)

    result_data = [{"TimeOfSample": row[0], "SampleValue": row[1]} for row in cursor.fetchall()]
    conn.close()
    return result_data

def send_data_to_collect_api(data, url, token, params):
    measurements = [
        {"value": row["SampleValue"], "timestamp": row["TimeOfSample"].strftime("%Y-%m-%dT%H:%M:%SZ")}
        for row in data
    ]
    payload = {
        "measurements": measurements,
        "name": params["name"],
        "hostDevice": params["hostDevice"],
        "device": params["device"],
        "log": params.get("log", 0.0),
        "point": params.get("point", ""),
        "id_equipment": params["id_equipment"],
        "id_parameter": params["id_parameter"],
        "measurement": params["name"]
    }
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        print(f"Data for {params['name']} sent successfully.")
    else:
        print(f"Failed to send data for {params['name']}. Status code: {response.status_code}")

if __name__ == "__main__":
    collect_url = "https://api.sparksentry.fr/api/v1/collect"
    login_url = "https://api.sparksentry.fr/api/v1/login"
    email = "jb@sparksentry.com"
    password = "root"

    try:
        token = fetch_jwt_token(login_url, email, password)
        for param in parameters:
            print(f"Processing: {param['name']}")
            data = fetch_values(param["mdb_path"], param["table_name"], mode="last48h")
            if data:
                print(f"Retrieved {len(data)} records for {param['name']}. Sending to API...")
                send_data_to_collect_api(data, collect_url, token, param)
            else:
                print(f"No data found for {param['name']}.")
    except Exception as e:
        print(f"An error occurred: {e}")
