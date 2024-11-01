#Battery Temperature Visualization Tool - User Guide

Welcome to the Battery Temperature Visualization Tool! This guide will help you set up and use the tool on a Windows computer. The tool is designed for mechanical engineers with basic computer skills, so no programming experience is required.

##Table of Contents

	-   [Introduction](#introduction)
	-   [Installation Steps] (#installation-steps)
	    -   [1. Install Python](#1-install-python)
        -   [2. Install Required Python Packages](#2-install-required-python-packages)
	-	[Preparing Your Data](#preparing-your-data)
	    -	Select Your Data from the Settings Program
	-	[Running the Tool](#running-the-tool)
	    -	Run the Main Program
	-	Troubleshooting

Introduction

The Battery Temperature Visualization Tool is a Python script that processes battery temperature data from a database and generates interactive visualizations. The tool helps you analyze temperature distribution across different layers of a battery module over time.

Installation Steps

1. Install Python

Python is the programming language used to run the tool.

Download Python 3.10 or later:

	•	Go to the official Python website.
	•	Click on “Download Python 3.10.x” (or the latest version available).

Run the Installer:

	•	Locate the downloaded file (e.g., python-3.10.x.exe) and double-click it.
	•	Important: On the first installation screen, check the box that says “Add Python 3.10 to PATH”.
	•	Click “Install Now” and follow the prompts.

Verify the Installation:

	1.	Open the Command Prompt:
	•	Press Win + R, type cmd, and press Enter.
	2.	Check Python Version:
	•	Type python --version and press Enter.
	•	You should see a response like Python 3.10.x.

2. Install Required Python Packages

The tool uses several Python libraries that need to be installed.

Open the Command Prompt:

	•	Press Win + R, type cmd, and press Enter.

Navigate to the Unzipped Folder:

	1.	Type dir to see all directories.
	2.	Type cd to move into a folder.
	•	Example: cd Downloads\bat_temp_test-main to enter the project folder in Downloads.
	3.	Type cd.. to go back one level.

Install Packages Using pip:

	•	Type the following command and press Enter: pip install -r requirements.txt
    •	Wait for the installation to complete.

Preparing Your Data

Select Your Data from the Settings Program

	1.	Navigate to your project directory where bat_temp_test-main is located:
	•	Use the commands from Navigate to the Unzipped Folder.
	2.	Run the settings.py Program:
	•	In the Command Prompt, type the following command and press Enter: python settings.py
    •	Follow the prompts in the settings program to select your data.

Running the Tool

Run the Main Program

	1.	Navigate to your project directory where bat_temp_test-main is located:
	•	Use the commands from Navigate to the Unzipped Folder.
	2.	Run the thermal_dynamics_HVB.py Program:
	•	In the Command Prompt, type the following command and press Enter: python thermal_dynamics_HVB.py
    •	The script will start running. You may see messages indicating that data is being loaded or processed.

Interact with the Visualization:

	•	A window will open displaying the battery temperature visualization.
	•	Use the slider at the bottom to navigate through time.
	•	Click “Play/Pause” to start or stop the animation.
	•	Use “Fast Forward” and “Rewind” buttons to navigate quickly.

Closing the Visualization:

	•	When you’re done, you can close the window by clicking the “X” in the top-right corner.

Troubleshooting

If you encounter issues, here are some common solutions:

Problem: “python is not recognized as an internal or external command”

	•	Solution: Python is not added to your system’s PATH. Reinstall Python and ensure you check the box “Add Python 3.10 to PATH” during installation.

Problem: ImportError messages when running the script

	•	Solution: Ensure all required packages are installed. Run: pip install -r requirements.txt
Problem: FileNotFoundError related to data files

	•	Solution: Verify that your database file, lookup table, and background image are in the correct locations as specified in the config.json file.

