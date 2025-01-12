@echo off
:: Read the value of the img_path from latest.txt
set /p IMG_PATH=<latest.txt

:: Check if the IMG_PATH is empty
if "%IMG_PATH%"=="" (
    echo Error: latest.txt is empty or the image path is not specified.
    pause
    exit /b
)

:: Run the Python script with the value from latest.txt
python.exe .\__init__.py --img_path "%IMG_PATH%"
