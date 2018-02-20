set LIB_NAME=ArduinoRpc
set LIB_SRC_DIR=%SRC_DIR%\arduino_rpc\Arduino\library\%LIB_NAME%
set INCLUDE_DIR=%PREFIX%\Library\include\Arduino

@echo off
setlocal enableextensions
md "%INCLUDE_DIR%"
endlocal

REM Generate Arduino `library.properties` file
python -m paver generate_arduino_library_properties
if errorlevel 1 exit 1
REM Copy Arduino library to Conda include directory
xcopy /S /Y /I /Q "%LIB_SRC_DIR%" "%INCLUDE_DIR%\%LIB_NAME%"
if errorlevel 1 exit 1

REM Generate `setup.py` from `pavement.py` definition.
python -m paver generate_setup

REM Install source directory as Python package.
python setup.py install --single-version-externally-managed --record record.txt
if errorlevel 1 exit 1
