# 📊 Project: Data Collector with API Integration

This project is a Python application designed to collect data from SQL Server databases or MDB files and send it to a REST API for processing.

### ✨ Features
- 🔑 API Authentication: Retrieve a JWT token for secure data transmission.
- Data Collection:
- Extract data from SQL Server databases.
- Extract data from Microsoft Access (MDB) files.
- Data Transmission: Transform and send the collected data to a REST API.
- Configurable: All settings are defined via a config.json file.

## 🛠️ Installation

##### ✅ Prerequisites:
 - 🐍 Python 3.8 or later
 - Required Python modules (see below)
 - Drivers for SQL Server and Microsoft Access:
 - SQL Server Native Client (Windows)
 - Microsoft Access ODBC Driver (*.mdb, *.accdb)

📦 Install Python Dependencies

Install the required dependencies using pip:

```bash
pip install -r requirements.txt
```


### 📁 Required Files 
- app.py: Main script
- fig.json: Configuration file (example below)
- .spec: PyInstaller configuration for generating an executable

## 🚀 Usage

### 1️⃣ Configure

Create a config.json file at the project root with the following structure:

```json
{
    "api": {
        "login_url": "https://api.example.com/login",
        "collect_url": "https://api.example.com/collect",
        "email": "user@example.com",
        "password": "password123"
    },
    "sql_server": {
        "server": "your_sql_server",
        "database": "your_database",
        "username": "your_username",
        "password": "your_password"
    },
    "parameters": [
        {
            "name": "Temperature",
            "database_type": "sqlserver",
            "table_name": "TemperatureData",
            "id_equipment": 1,
            "id_parameter": 101,
            "hostDevice": "Device_01",
            "device": "Sensor_01",
            "log": 0.0,
            "point": "Room_1"
        },
        {
            "name": "Humidity",
            "database_type": "mdb",
            "mdb_path": "path_to_your_file.mdb",
            "table_name": "HumidityData",
            "id_equipment": 2,
            "id_parameter": 102,
            "hostDevice": "Device_02",
            "device": "Sensor_02",
            "log": 0.0,
            "point": "Room_2"
        }
    ]
}
````

### 2️⃣ Run the Application

Run the script with:

```bash
python app.py
```

### #️⃣ Generate an Executable

To create an executable using PyInstaller:
```bash
pyinstaller app.spec
```

The executable will be available in the dist/ directory.

### 📂 Project Structure

	project/
	│
	├── app.py              # Main script
	├── app.spec            # PyInstaller configuration
	├── config.json         # Configuration file
	├── requirements.txt    # List of dependencies
	└── dist/               # Directory for the generated executable

🛠️ Troubleshooting
1.	SQL Server Connection Issues:
   - Ensure the SQL Server Native Client driver is installed. 
   - Verify the server, username, and password values in config.json.
2.	MDB File Issues:
- Make sure the MDB file exists and the path is correct.
- Ensure the Microsoft Access ODBC driver is installed.
3.	API Transmission Issues:
- Verify the API URLs in config.json.
- Check API authentication permissions and endpoint availability.

## 🤝 Contribution

Contributions are welcome! Feel free to submit issues or pull requests to improve the project.

## 📜 License

This project is licensed under the MIT License. See the LICENSE file for details.
