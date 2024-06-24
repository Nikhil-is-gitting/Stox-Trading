@echo off

REM Set the Python path to the one used by your IDE
set PYTHON_PATH="C:\Users\vikky\OneDrive\Desktop\Hoodup Strategies\.venv\Scripts\python.exe"

REM Navigate to the directory containing the Python script
cd C:\Users\vikky\OneDrive\Desktop\Hoodup Strategies\Strategies

REM Run the Streamlit app using the specified Python executable
%PYTHON_PATH% -m streamlit run supertrendstrategy.py

REM Optionally, keep the command prompt window open to see the output
pause
