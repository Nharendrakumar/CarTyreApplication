# XXX Tyres Chatbot

Step-by-Step Instructions

Install Ollama (for Local LLM):

Download and install Ollama from https://ollama.com/ (free, open-source).
Open a terminal and run: ollama run llama3 (downloads the Llama3 model if not present). This provides the LLM for agentic tasks. Keep Ollama running in the background while using the app.
Note: Llama3 is open-source; you can swap with other models like Mistral via ollama run mistral.


Set Up Python Environment:

Ensure Python 3.10+ is installed (free from python.org).
Create a virtual environment: python -m venv venv then source venv/bin/Activate.ps1 (Linux/Mac) or .\venv\Scripts\Activate.ps1 (Windows).
Install dependencies: pip install -r requirements.txt.


Create the Files:

Copy the code below into each file in the xxx_tyres_app directory.


Run the Application:

In the terminal: streamlit run app.py.
Open the browser URL shown (e.g., http://localhost:8501).
Test: Chat with inputs like "Toyota Camry 2023, 19-inch tyres, zip 90210". The agent will scrape prices, match/optimize, and offer scheduling.


Data Updates (Manual/Automated):

Run python scraper.py manually to update cached prices (saves to a local JSON file).
For automation: Use system cron jobs (free) to run it daily, e.g., crontab -e and add 0 0 * * * /path/to/python /path/to/scraper.py.


Testing and Customization:

Test price matching: Ensure scraping works (adjust selectors in scraper.py if sites change).
After-hours: Set your system time to test.
Optimize: Add more sites to scrape in scraper.py for better price matching.
Debugging: If Ollama is slow, use a smaller model like ollama run phi.

Free, open-source tyre sales app.



## Commands to run application in different terminals
Terminal 1: ollama run llama3

Terminal 2:
cd D:\CarTyresApplication
.\venv\Scripts\Activate.ps1
python scraper.py

Terminal 3: 
cd D:\CarTyresApplication
.\venv\Scripts\Activate.ps1
streamlit run app.py

