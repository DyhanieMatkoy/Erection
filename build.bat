@echo off
echo Building Construction Time Management System...

if not exist build mkdir build
cd build

cmake .. -G "MinGW Makefiles"
if %errorlevel% neq 0 (
    echo CMake configuration failed!
    exit /b %errorlevel%
)

cmake --build .
if %errorlevel% neq 0 (
    echo Build failed!
    exit /b %errorlevel%
)

echo Build completed successfully!
cd ..
