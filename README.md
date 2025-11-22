### Requirements

- Python 3.7+
- Chrome Browser

### Isolation environment (optional)

```bash
python -m venv myspace
```

```bash
source myspace/bin/activate  # On Mac/Linux
myspace\Scripts\activate  # On Windows
```

### Virtual machine

##### Install packages

```bash
pip install -r requirements.txt
```

##### Run

- From command line:

```bash
python index.py
```

- Arguments input fields:

- `iso_path`: Path to Windows ISO file (Ex: C:\path\to\file.iso)

- `name`: Virtual machine name (Ex: 2022-example.com)
- `sock`: Socket5 like format `host:port:user:password`
- `address`: Address (Ex: Louisiana)

##### 🔨 Build

```bash
cd vm
./build.bat
```

hoặc

```bash
cd vm
pyinstaller build.spec --clean
```

##### ⚠️ Notes

- File executable needs the `templates` folder at the same level to function correctly
- The console window is enabled to display logs and receive command-line arguments
- Ensure the template files (.png) are in the templates folder before running

### Store

##### Install packages

```bash
pip install selenium
pip install webdriver-manager
# or
pip install -r requirements.txt
```

##### Build

Double click to **`build.bat`** or run

```bash
pyinstaller build.spec --clean
```

2. The exe file will be created in the `dist/autify.exe` directory

3. Copy the `config.json` file to the same directory as the exe file (if not already present)

##### Start

Click to .exe in **`/dist/autify.exe`** or run

```bash
python gui.py
```

or run with CLI

```bash
python index.py
```

##### Usage

1. **Start application**: Double click to `autify.exe`

2. **Check infomation**: The application will automatically load store information from the `config.json` file

3. **Login**: Click to button "🔐 Login to Shopify" to login

4. **Running tasks**: After successful login, click on the task buttons to execute:

   - 📦 Install Apps
   - 🛠️ DSers (progress)
   - 🌍 Markets
   - 📜 Policies
   - 📄 Pages
   - 🚚 Shipping (progress)
   - ⚙️ Preferences

5. **Monitoring logs**: View the Activity Log below to track progress

##### Notes

- The `config.json` file must be in the same folder as the exe file
- The Chrome browser will automatically open upon login
- The session is saved in the `selenium_data` folder
- You can run multiple tasks consecutively after logging in

##### Troubleshooting

**Error "No credentials found":**

- Check if the `config.json` file exists and ensure that it has the correct format with the fields: email, password, storeId

**WebDriver Error:**

- Ensure the Chrome browser is installed
- Check internet connection
- Try running the application again

**Task Error:**

- View detailed logs in the Activity Log
- Ensure you are logged in before running a task
- Check for a stable internet connection
