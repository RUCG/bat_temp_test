Introduction

Welcome to the Battery Temperature Visualization Tool! This guide will help you set up and use the tool on a Windows computer. It’s designed for mechanical engineers with basic computer skills—no programming experience required.

Prerequisites

Before you begin, make sure you have the following:

	•	A Windows computer.
	•	An internet connection to download the necessary software.
	•	Administrative privileges to install software.
	•	Basic familiarity with the Command Prompt (don’t worry—we’ll guide you through it!).

Installation Steps

1. Install Python

Python is required to run the tool.

	1.	Download Python 3.10 or later:
	•	Visit the official Python website.
	•	Download the latest Python 3.10.x version.
	2.	Run the Installer:
	•	Locate the downloaded file (e.g., python-3.10.x.exe) and double-click to open it.
	•	Important: Check the box that says “Add Python 3.10 to PATH”.
	•	Click Install Now and follow the prompts.
	3.	Verify the Installation:
	•	Open the Command Prompt by pressing Win + R, typing cmd, and pressing Enter.
	•	Run the following command: python --version

    	•	You should see output like Python 3.10.x, confirming the installation.

2. Install Required Python Packages

The tool uses several Python libraries that need to be installed.

	1.	Open the Command Prompt:
	•	Press Win + R, type cmd, and press Enter.
	2.	Navigate to the Project Directory:
	•	Use these commands to navigate:
	•	dir: Lists all directories in the current folder.
	•	cd folder_name: Enters the specified folder.
	•	Example: cd downloads\bat_temp_test-main
	•	cd ..: Goes up one directory level.
	3.	Install Packages Using requirements.txt:
	•	Run the following command in the Command Prompt: pip install -r requirements.txt

    	•	Wait for the installation to complete.

Configuring Your Data

To use your specific data with the tool, you’ll need to configure the paths.

	1.	Run the Settings Program:
	•	In Command Prompt, navigate to the project directory (bat_temp_test-main).
	•	Run: python settings.py

    •	Follow the on-screen instructions to select your data files and configure settings. This will create a config.json file in the project directory.

Running the Main Program

Once you’ve configured your data, you’re ready to run the main program.

	1.	Navigate to the Project Directory.
	2.	Run the Main Program:
	•	In Command Prompt, type the following command: python thermal_dynamics_HVB.py
    •	Press Enter to start the visualization tool.


