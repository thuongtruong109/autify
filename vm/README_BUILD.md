# VM Automation EXE

## 📦 Build thành công!

File executable đã được tạo tại: `dist\vm_automation.exe`

## 🚀 Cách sử dụng

### Chạy từ command line:

```bash
vm_automation.exe <name> <sock> <address>
```

### Ví dụ:

```bash
vm_automation.exe 2022-example.com 185.253.122.152:5961:user:pass Louisiana
```

### Tham số:

- `<name>`: Tên VM (ví dụ: 2022-example.com)
- `<sock>`: Thông tin socket theo định dạng `host:port:user:password`
- `<address>`: Địa chỉ (ví dụ: Louisiana)

## 📂 Cấu trúc

```
vm/
├── dist/
│   ├── vm_automation.exe    # Executable chính
│   └── templates/           # Thư mục templates (được copy tự động)
├── build.spec               # Cấu hình PyInstaller
├── build.bat               # Script build
├── index.py                # Source code chính
├── watcher.py              # Module watcher
└── requirements.txt        # Dependencies
```

## 🔨 Build lại

Để build lại executable, chạy:

```bash
cd vm
./build.bat
```

hoặc

```bash
cd vm
pyinstaller build.spec --clean
```

## 📋 Dependencies

- pyautogui
- numpy
- opencv-python
- pillow
- pygetwindow
- pyperclip

## ⚠️ Lưu ý

- File executable cần thư mục `templates` ở cùng cấp để hoạt động đúng
- Console window được bật để hiển thị log và nhận command-line arguments
- Đảm bảo các file template (.png) có trong thư mục templates trước khi chạy
