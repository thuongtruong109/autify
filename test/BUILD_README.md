# VM Automation - Build Guide

## Cấu trúc dự án sau khi tích hợp GUI

### Files chính:

- `index.py` - Script chính chứa logic automation
- `launcher.py` - Module tích hợp GUI vào exe (mới tạo)
- `gui.py` - File GUI độc lập (giữ nguyên)
- `watcher.py` - Module theo dõi màn hình
- `build.spec` - Cấu hình PyInstaller (đã cập nhật)
- `build.bat` - Script build exe

### Cách hoạt động:

#### 1. Khi chạy file EXE (`autify_vm.exe`):

- EXE sẽ tự động hiển thị GUI để nhập thông tin
- Người dùng nhập: Name, Sock, Address
- Nhấn "Start Automation" để bắt đầu
- Automation sẽ chạy với thông tin đã nhập

#### 2. Khi chạy file `gui.py` riêng lẻ:

- Có thể chạy độc lập: `python gui.py`
- Giao diện tương tự nhưng chỉ để test/demo

### Build lại EXE:

```batch
cd vm
./build.bat
```

Hoặc:

```batch
pyinstaller build.spec --clean
```

### Cấu trúc đã được tích hợp:

```
vm/
├── index.py          # Main automation script
├── launcher.py       # GUI launcher (tích hợp vào exe)
├── gui.py           # Standalone GUI (giữ nguyên, có thể chạy riêng)
├── watcher.py       # Screen watcher module
├── build.spec       # PyInstaller config (đã cập nhật)
├── build.bat        # Build script
├── requirements.txt
├── templates/       # Image templates
└── dist/
    ├── autify_vm.exe  # Executable với GUI tích hợp
    └── templates/     # Templates folder (auto copied)
```

### Thay đổi trong build.spec:

```python
a = Analysis(
    ['index.py', 'launcher.py', 'gui.py'],  # Thêm launcher.py và gui.py
    # ...
    hiddenimports=[
        # ... các imports khác
        'tkinter',           # Thêm tkinter
        'tkinter.ttk',       # Thêm ttk
        'tkinter.messagebox', # Thêm messagebox
        'threading',         # Thêm threading
        'launcher',          # Thêm launcher module
        'gui',              # Thêm gui module
    ],
    # ...
)
```

### Lưu ý:

1. **File gui.py vẫn giữ nguyên** - có thể chạy độc lập nếu cần
2. **Launcher.py** - là module mới để tích hợp GUI vào exe
3. **index.py** - đã import launcher để hiển thị GUI khi chạy
4. **EXE đã bao gồm GUI** - không cần file Python nào khác để chạy

### Test EXE:

Sau khi build, chạy:

```
cd dist
./autify_vm.exe
```

GUI sẽ tự động hiển thị để nhập thông tin!

### Troubleshooting:

Nếu gặp lỗi khi build:

1. Xóa folders: `build/`, `dist/`, `__pycache__/`
2. Chạy lại: `./build.bat`

Nếu GUI không hiển thị trong exe:

1. Kiểm tra `hiddenimports` trong `build.spec`
2. Đảm bảo `tkinter` đã được cài đặt trong Python
