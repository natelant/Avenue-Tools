# Error Summary Script Instructions

## Introduction

The Error Summary Script is a tool designed to analyze simulation error files (`.err`) and generate a comprehensive Excel report of warnings and issues. It specifically:

- Analyzes lane change failures and their locations
- Tracks routing-related warnings
- Monitors vehicle input issues
- Consolidates warnings across multiple simulation runs
- Generates an organized Excel report with sortable data

This tool is particularly useful for:
- Identifying problematic areas in your traffic network
- Debugging recurring simulation issues
- Analyzing patterns in lane change failures
- Monitoring vehicle input performance

## Prerequisites

1. Install Python
   - Download Python from [python.org](https://python.org/downloads/)
   - During installation, make sure to check "Add Python to PATH"
   - Verify installation by opening a command prompt/terminal and typing:
     ```bash
     python --version
     ```

2. Install Required Libraries
   - Open a command prompt/terminal
   - Navigate to the script directory:
     ```bash
     cd path/to/script/folder
     ```
   - Install requirements:
     ```bash
     pip install -r requirements.txt
     ```

## Running the Script

1. Open a command prompt/terminal

2. Navigate to the script directory:
   ```bash
   cd path/to/script/folder
   ```

3. Run the script:
   ```bash
   python error_summary.py
   ```

4. When prompted, enter the path to your base folder containing the `.results` folder
   - Example: `C:\Projects\MyScenario`
   - The script expects your folder to contain a subfolder named `[FolderName].results` with `.err` files

5. The script will:
   - Process all `.err` files in the `.results` folder
   - Create an Excel file named `error_summary_[FolderName].xlsx`
   - Automatically open the Excel file when complete

## Output Excel File

The generated Excel file contains three sheets:
1. **Lane Change**: Summary of lane change warnings by location
2. **Routing**: Detailed routing information for warnings
3. **Vehicle Input**: Summary of remaining vehicles at inputs

## Troubleshooting

- If you get "command not found" for Python, ensure Python is properly installed and added to PATH
- If you get import errors, verify that all requirements were installed successfully
- If the script can't find the folder, check that the path is correct and includes no trailing slashes
