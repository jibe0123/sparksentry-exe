import os
import json
import pyodbc
import requests
from datetime import datetime, timedelta

# Load configurations from external JSON file
def load_config(config_path="config.json"):
    """
    Load configuration from a JSON file.

    Args:
        config_path (str): Path to the configuration file.

    Returns:
        dict: Configuration data.
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file {config_path} not found.")
    with open(config_path, "r") as config_file:
        return json.load(config_file)

# Authenticate and retrieve a JWT token
def fetch_jwt_token(login_url, email, password):
    credentials = {"email": email, "password": password}
    response = requests.post(login_url, json=credentials)
    if response.status_code == 200:
        print("Successfully retrieved JWT token.")
        return response.json().get("data")
    else:
        raise Exception(f"Failed to retrieve token: {response.status_code}, {response.text}")

# Fetch data from a SQL Server database
def fetch_sql_server_data(config, table_name, mode="last48h"):
    conn_str = f"DRIVER={{SQL Server Native Client 11.0}};SERVER={config['server']};DATABASE={config['database']};UID={config['username']};PWD={config['password']}"
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

# Fetch data from an MDB file
def fetch_mdb_data(mdb_file_path, table_name, mode="last48h"):
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

# Send data to the API
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

# Main function
if __name__ == "__main__":
    config = load_config()
    api_config = config["api"]
    sql_server_config = config["sql_server"]
    parameters = config["parameters"]

    try:
        token = fetch_jwt_token(api_config["login_url"], api_config["email"], api_config["password"])

        for param in parameters:
            print(f"Processing: {param['name']}")
            try:
                if param["database_type"] == "sqlserver":
                    data = fetch_sql_server_data(sql_server_config, param["table_name"], mode="last48h")
                elif param["database_type"] == "mdb":
                    data = fetch_mdb_data(param["mdb_path"], param["table_name"], mode="last48h")
                else:
                    raise ValueError(f"Unknown database type for parameter {param['name']}.")

                if data:
                    print(f"Retrieved {len(data)} records for {param['name']}. Sending to API...")
                    send_data_to_collect_api(data, api_config["collect_url"], token, param)
                else:
                    print(f"No data found for {param['name']}.")
            except Exception as db_error:
                print(f"Error processing {param['name']}: {db_error}")

    except Exception as e:
        print(f"An error occurred: {e}")