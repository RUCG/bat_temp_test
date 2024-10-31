# Battery Temperature Visualization Tool - User Guide

## Table of Contents
- [Introduction](#introduction)
- [Prerequisites](#prerequisites)
- [Installation Steps](#installation-steps)
  - [1. Install Python](#1-install-python)
  - [2. Install Required Python Packages](#2-install-required-python-packages)
- [Preparing Your Data](#preparing-your-data)
  - [1. Database File](#1-database-file)
  - [2. Lookup Table File](#2-lookup-table-file)
  - [3. Configuration File](#3-configuration-file)
  - [4. Background Image](#4-background-image)
- [Running the Tool](#running-the-tool)
- [Understanding the Output](#understanding-the-output)
- [Requirements](#requirements)
  - [Hardware Requirements](#hardware-requirements)
  - [Software Requirements](#software-requirements)
- [Troubleshooting](#troubleshooting)
- [Frequently Asked Questions](#frequently-asked-questions)
- [Support](#support)

---

## Introduction

Welcome to the **Battery Temperature Visualization Tool**! This guide will help you set up and use the tool on a Windows computer. The tool is designed for mechanical engineers with basic computer skills, so no programming experience is required.

## Prerequisites

Before you begin, ensure you have the following:
- A Windows computer.
- An internet connection to download necessary software.
- Administrative privileges to install software.
- Basic understanding of using the Command Prompt (don't worry—we'll guide you!).

## Installation Steps

### 1. Install Python

Python is the programming language used to run the tool.

1. **Download Python 3.10 or later:**
   - Go to the [official Python website](https://www.python.org/downloads/windows/).
   - Click on **"Download Python 3.10.x"** (or the latest version available).
   
2. **Run the Installer:**
   - Locate the downloaded file (e.g., `python-3.10.x.exe`) and double-click it.
   - **Important:** On the first installation screen, check the box that says **"Add Python 3.10 to PATH"**.
   - Click **"Install Now"** and follow the prompts.

3. **Verify the Installation:**
   - Open the **Command Prompt** by pressing `Win + R`, typing `cmd`, and pressing **Enter**.
   - Type `python --version` and press **Enter**.
   - You should see a response like `Python 3.10.x`.


### 2. Install Required Python Packages

The tool uses several Python libraries that need to be installed.

1. **Open the Command Prompt:**
   - Press `Win + R`, type `cmd`, and press **Enter**.

2. **head to the unziped folder:**
    - type `dir` to see all directorys
    - type `cd` to move into a folder
        - eg: `cd downloads\bat_temp_test-main` to enter the project folder in downloads
    - type `cd..` to go back one level

3. **Install Packages Using pip:**
    - type `pip install -r requirements.txt`

   - Wait for the installation to complete.


## Select Your Data from the settings programm

1. **go to your directory where bat_temp_test-main is located**
    - use the commands from 2.2

2. **run the program settings.py**
    - type `python settings.py` and hit enter

## Run the main Program

1. **go to your directory where bat_temp_test-main is located**
    - use the commands from 2.2

2. **run the programm thermal_dynamics_HVB.py**
    - type `python thermal_dynamics_HVB.py` and hit enter





## Preparing Your Data

Before running the tool, you need to have your data files ready.

### 1. Database File
- **File Needed:** A SQLite database file (e.g., `mf4_data.db`) containing the battery temperature data.
- **Action:** Place the database file in a folder where you can easily locate it (e.g., `C:\BatteryData\`).

### 2. Lookup Table File
- **File Needed:** A lookup table file in Parquet or CSV format (e.g., `db_lookup_table.parquet` or `db_lookup_table.csv`).
- **Action:** Place the lookup table file in the same folder as the database file.

### 3. Configuration File
- **File Needed:** A JSON configuration file named `config.json`.
- **Action:** Create a file named `config.json` in the same folder as the script. This file tells the tool where to find your data files and other settings.

**Sample `config.json` Content:**
```json
{
  "db_path": "C:\\BatteryData\\mf4_data.db",
  "lookup_table_path": "C:\\BatteryData\\db_lookup_table.parquet",
  "file_id": "YourFileID.MF4",
  "vmin": 15.0,
  "vmax": 40.0
}