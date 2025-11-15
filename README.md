### Requirements

- Python 3.7+
- Chrome Browser
- Turn off unikey app (avoid conflict with typing input)

### Isolation environment (optional)

```bash
python -m venv automation-env
```

```bash
source automation-env/bin/activate  # On Mac/Linux
automation-env\Scripts\activate  # On Windows
```

### Virtual machine

##### Install packages

```bash
pip install pyautogui
pip install numpy
pip install opencv-python
pip install pillow
pip install pygetwindow
pip install pyperclip
```

##### Run

- From command line:

```bash
python index.py  <name> <sock> <address>
```

- Example:

```bash
python index.py 2022-example.com 185.253.122.152:5961:lkqbgbdk:klwsil8ci4hw Louisiana
# 193.160.82.72:6044:lkqbgbdk:klwsil8ci4hw
```

- Arguments

- `<name>`: Tên VM (ví dụ: 2022-example.com)
- `<sock>`: Thông tin socket theo định dạng `host:port:user:password`
- `<address>`: Địa chỉ (ví dụ: Louisiana)

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

## ⚠️ Notes

- File executable cần thư mục `templates` ở cùng cấp để hoạt động đúng
- Console window được bật để hiển thị log và nhận command-line arguments
- Đảm bảo các file template (.png) có trong thư mục templates trước khi chạy

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

2. File exe sẽ được tạo trong thư mục `dist/autify.exe`

3. Copy file `config.json` vào cùng thư mục với file exe (nếu chưa có)

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

- Check if the `config.json` file exists
- Ensure the `config.json` file has the correct format with the fields: email, password, storeId

**WebDriver Error:**

- Ensure the Chrome browser is installed
- Check internet connection
- Try running the application again

**Task Error:**

- View detailed logs in the Activity Log
- Ensure you are logged in before running a task
- Check for a stable internet connection

<!-- input("Đã xảy ra lỗi cần đóng và chạy lại...")
pyautogui.scroll(-300)
pyautogui.scroll(300)
pyautogui.doubleClick()
pyautogui.write('Automation_Guide.txt', interval=0.1) -->
