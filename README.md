\documentclass{article}
\usepackage[utf8]{inputenc}
\usepackage{hyperref}
\usepackage{listings}
\usepackage{xcolor}
\usepackage{graphicx}
\usepackage{tocbibind}

\title{Battery Temperature Visualization Tool - User Guide}
\author{}
\date{}

\begin{document}

\maketitle

\tableofcontents

\section{Introduction}

Welcome to the \textbf{Battery Temperature Visualization Tool}! This guide will help you set up and use the tool on a Windows computer. The tool is designed for mechanical engineers with basic computer skills, so no programming experience is required.

\section{Prerequisites}

Before you begin, ensure you have the following:

\begin{itemize}
    \item A Windows computer.
    \item An internet connection to download necessary software.
    \item Administrative privileges to install software.
    \item Basic understanding of using the Command Prompt (don't worry—we'll guide you!).
\end{itemize}

\section{Installation Steps}

\subsection{1. Install Python}

Python is the programming language used to run the tool.

\begin{enumerate}
    \item \textbf{Download Python 3.10 or later:}
    \begin{itemize}
        \item Go to the \href{https://www.python.org/downloads/windows/}{official Python website}.
        \item Click on \textbf{"Download Python 3.10.x"} (or the latest version available).
    \end{itemize}
    \item \textbf{Run the Installer:}
    \begin{itemize}
        \item Locate the downloaded file (e.g., \texttt{python-3.10.x.exe}) and double-click it.
        \item \textbf{Important:} On the first installation screen, check the box that says \textbf{"Add Python 3.10 to PATH"}. This allows you to run Python from the Command Prompt.
        \item Click \textbf{"Install Now"} and follow the prompts to complete the installation.
    \end{itemize}
    \item \textbf{Verify the Installation:}
    \begin{itemize}
        \item Open the \textbf{Command Prompt}:
        \begin{itemize}
            \item Press \texttt{Win + R}, type \texttt{cmd}, and press \textbf{Enter}.
        \end{itemize}
        \item Type \texttt{python --version} and press \textbf{Enter}.
        \item You should see a response like \texttt{Python 3.10.x}.
    \end{itemize}
\end{enumerate}

\subsection{2. Install Required Python Packages}

The tool uses several Python libraries that need to be installed.

\begin{enumerate}
    \item \textbf{Open the Command Prompt:}
    \begin{itemize}
        \item Press \texttt{Win + R}, type \texttt{cmd}, and press \textbf{Enter}.
    \end{itemize}
    \item \textbf{Install Packages Using pip:}
    \begin{itemize}
        \item Type the following command and press \textbf{Enter}:

        \begin{lstlisting}[language=bash]
pip install pandas matplotlib numpy sqlalchemy
        \end{lstlisting}
        \item Wait for the installation to complete. You should see messages indicating successful installations.
    \end{itemize}
\end{enumerate}

\section{Preparing Your Data}

Before running the tool, you need to have your data files ready.

\subsection{1. Database File}

\begin{itemize}
    \item \textbf{File Needed:} A SQLite database file (e.g., \texttt{mf4\_data.db}) containing the battery temperature data.
    \item \textbf{Action:} Place the database file in a folder where you can easily locate it (e.g., \texttt{C:\textbackslash BatteryData\textbackslash}).
\end{itemize}

\subsection{2. Lookup Table File}

\begin{itemize}
    \item \textbf{File Needed:} A lookup table file in Parquet or CSV format (e.g., \texttt{db\_lookup\_table.parquet} or \texttt{db\_lookup\_table.csv}).
    \item \textbf{Action:} Place the lookup table file in the same folder as the database file.
\end{itemize}

\subsection{3. Configuration File}

\begin{itemize}
    \item \textbf{File Needed:} A JSON configuration file named \texttt{config.json}.
    \item \textbf{Action:} Create a file named \texttt{config.json} in the same folder as the script. This file tells the tool where to find your data files and other settings.
\end{itemize}

\textbf{Sample \texttt{config.json} Content:}

\begin{lstlisting}[language=json]
{
  "db_path": "C:\\BatteryData\\mf4_data.db",
  "lookup_table_path": "C:\\BatteryData\\db_lookup_table.parquet",
  "file_id": "YourFileID.MF4",
  "vmin": 15.0,
  "vmax": 40.0
}
\end{lstlisting}

\begin{itemize}
    \item \textbf{db\_path:} Full path to your database file.
    \item \textbf{lookup\_table\_path:} Full path to your lookup table file.
    \item \textbf{file\_id:} The identifier of the data file you want to analyze (replace \texttt{"YourFileID.MF4"} with your actual file ID).
    \item \textbf{vmin} and \textbf{vmax:} Minimum and maximum temperature values for the visualization scale.
\end{itemize}

\subsection{4. Background Image}

\begin{itemize}
    \item \textbf{File Needed:} An image file named \texttt{coolingplate\_edited.png} that represents the battery layout.
    \item \textbf{Action:} Place the image file in the same folder as the script.
\end{itemize}

\section{Running the Tool}

Now that everything is set up, you're ready to run the tool.

\begin{enumerate}
    \item \textbf{Locate the Script:}
    \begin{itemize}
        \item Ensure the Python script file (e.g., \texttt{battery\_visualization.py}) is saved in a folder (e.g., \texttt{C:\textbackslash BatteryData\textbackslash}).
    \end{itemize}
    \item \textbf{Open the Command Prompt:}
    \begin{itemize}
        \item Press \texttt{Win + R}, type \texttt{cmd}, and press \textbf{Enter}.
    \end{itemize}
    \item \textbf{Navigate to the Script Directory:}
    \begin{itemize}
        \item In the Command Prompt, type the following command and press \textbf{Enter}:

        \begin{lstlisting}[language=bash]
cd C:\BatteryData\
        \end{lstlisting}

        \item Replace \texttt{C:\textbackslash BatteryData\textbackslash} with the path to the folder where your script is located.
    \end{itemize}
    \item \textbf{Run the Script:}
    \begin{itemize}
        \item Type the following command and press \textbf{Enter}:

        \begin{lstlisting}[language=bash]
python battery_visualization.py
        \end{lstlisting}

        \item The script will start running. You may see messages indicating that data is being loaded or processed.
    \end{itemize}
    \item \textbf{Interact with the Visualization:}
    \begin{itemize}
        \item A window will open displaying the battery temperature visualization.
        \item Use the slider at the bottom to navigate through time.
        \item Click \textbf{"Play/Pause"} to start or stop the animation.
        \item Use \textbf{"Fast Forward"} and \textbf{"Rewind"} buttons to navigate quickly.
        \item Hover over different layers to see detailed information.
    \end{itemize}
    \item \textbf{Closing the Visualization:}
    \begin{itemize}
        \item When you're done, you can close the window by clicking the \textbf{"X"} in the top-right corner.
    \end{itemize}
\end{enumerate}

\section{Understanding the Output}

The visualization displays several key pieces of information:

\begin{itemize}
    \item \textbf{Battery Layers:} Each subplot represents a layer of the battery module, showing temperature distribution.
    \item \textbf{Temperature Metrics:}
    \begin{itemize}
        \item \textbf{Mean Temperature}
        \item \textbf{Maximum Temperature}
        \item \textbf{Minimum Temperature}
        \item \textbf{Temperature Range}
        \item \textbf{Standard Deviation}
    \end{itemize}
    \item \textbf{Interactive Plot:}
    \begin{itemize}
        \item The bottom plot shows the \textbf{Cell Temperature Range} and the \textbf{Range of Mean Layer Temperatures} over time.
    \end{itemize}
    \item \textbf{Inlet/Outlet Temperatures and Coolant Flow:}
    \begin{itemize}
        \item Displayed at the top center of the visualization.
        \item \textbf{Q\_HVB:} Represents the calculated heat flux.
    \end{itemize}
\end{itemize}

\section{Requirements}

Here are the requirements for running the Battery Temperature Visualization Tool:

\subsection{Hardware Requirements}

\begin{itemize}
    \item Windows PC with at least 4 GB of RAM.
    \item Sufficient disk space to store the database and lookup table files.
\end{itemize}

\subsection{Software Requirements}

\begin{itemize}
    \item \textbf{Python 3.10} or later.
    \item Python packages:
    \begin{itemize}
        \item \texttt{pandas}
        \item \texttt{matplotlib}
        \item \texttt{numpy}
        \item \texttt{sqlalchemy}
    \end{itemize}
    \item Data files:
    \begin{itemize}
        \item SQLite database file (e.g., \texttt{mf4\_data.db})
        \item Lookup table file (e.g., \texttt{db\_lookup\_table.parquet} or \texttt{db\_lookup\_table.csv})
        \item Configuration file (\texttt{config.json})
        \item Background image (\texttt{coolingplate\_edited.png})
    \end{itemize}
\end{itemize}

\section{Troubleshooting}

If you encounter issues, here are some common solutions:

\subsection{Problem: "python is not recognized as an internal or external command"}

\textbf{Solution:} Python is not added to your system's PATH. Reinstall Python and ensure you check the box \textbf{"Add Python 3.10 to PATH"} during installation.

\subsection{Problem: ImportError messages when running the script}

\textbf{Solution:} Ensure all required packages are installed. Run:

\begin{lstlisting}[language=bash]
pip install pandas matplotlib numpy sqlalchemy
\end{lstlisting}

\subsection{Problem: FileNotFoundError related to data files}

\textbf{Solution:} Verify that your database file, lookup table, and background image are in the correct locations as specified in the \texttt{config.json} file.

\subsection{Problem: The visualization window does not appear}

\textbf{Solution:} There may be issues with the matplotlib backend. Ensure you're running the script in a standard Command Prompt and not within an environment that may interfere with GUI applications.

\section{Frequently Asked Questions}

\subsection{Q1: Can I use data files in formats other than SQLite and Parquet?}

\textbf{A:} The tool currently supports SQLite databases and Parquet or CSV lookup tables. If your data is in a different format, you may need to convert it.

\subsection{Q2: How can I adjust the temperature scale?}

\textbf{A:} Modify the \texttt{vmin} and \texttt{vmax} values in the \texttt{config.json} file to set the minimum and maximum temperatures for the visualization scale.

\subsection{Q3: Can I use a different background image?}

\textbf{A:} Yes, replace \texttt{coolingplate\_edited.png} with your own image, but ensure the file path in the script is updated accordingly.

\section{Support}

If you need further assistance:

\begin{itemize}
    \item \textbf{Contact the Support Team:}
    \begin{itemize}
        \item Email: \href{mailto:support@example.com}{support@example.com}
        \item Phone: +1-234-567-8900
    \end{itemize}
    \item \textbf{Additional Resources:}
    \begin{itemize}
        \item Python Documentation: \href{https://docs.python.org/3/}{https://docs.python.org/3/}
        \item Matplotlib Documentation: \href{https://matplotlib.org/stable/contents.html}{https://matplotlib.org/stable/contents.html}
    \end{itemize}
\end{itemize}

---

\textbf{Thank you for using the Battery Temperature Visualization Tool!} If you have suggestions or feedback, please let us know.

\end{document}