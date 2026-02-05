@echo off
REM Publication script for yfin-mcp (Windows)
REM This script builds and publishes the package to PyPI using uv

echo ========================================
echo Publishing yfin-mcp to PyPI
echo ========================================
echo.

REM Version bumping logic
set BUMP_TYPE=%1
if "%BUMP_TYPE%"=="major" goto :bump
if "%BUMP_TYPE%"=="minor" goto :bump
if "%BUMP_TYPE%"=="patch" goto :bump
goto :start_build

:bump
echo Step 0: Bumping version (%BUMP_TYPE%)...
uv run scripts/bump_version.py %BUMP_TYPE%
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Version bump failed.
    pause
    exit /b %ERRORLEVEL%
)
echo.

:start_build
echo Step 1: Cleaning dist directory...
if exist dist (
    rmdir /s /q dist
)

echo Step 2: Building package...
uv build
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Build failed. Aborting.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [SUCCESS] Build complete.
echo.

set /p CONFIRM="Do you want to publish to PyPI now? (y/n): "
if /i "%CONFIRM%" neq "y" (
    echo.
    echo [INFO] Publication cancelled by user.
    exit /b 0
)

echo.
echo Step 3: Publishing to PyPI via twine...
echo.
echo [TIP] PyPI authentication now REQUIRES API tokens.
echo [TIP] Username: '__token__'
echo [TIP] Password: 'pypi-YourTokenHere'
echo.

echo [INFO] Installing/Updating twine...
uv pip install twine

echo [INFO] Running twine upload...
uv run twine upload dist/*

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Publication failed.
    echo.
    echo [GUIDE] If you're using a token:
    echo        - Username: __token__
    echo        - Password: pypi-YOUR_TOKEN_STRING
    echo.
    echo [INFO] Current HOME is: %HOME%
    echo [INFO] Current USERPROFILE is: %USERPROFILE%
    echo.
    echo [TIP] Try setting the environment variables to automate:
    echo       set TWINE_USERNAME=__token__
    echo       set TWINE_PASSWORD=pypi-XXXXXX
    echo       ...and run this script again.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [SUCCESS] Package published successfully!
pause
