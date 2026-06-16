# captchabreakerbot
CAPTCHA breaker bot python tesseract OCR


How to Run the Project



1. Requirements
Make sure the following are installed:

-Python 3.10+
-pip 
-Google Chrome
-ChromeDriver (matching your Chrome version)
-Tesseract OCR

Windows default path:
C:\Program Files\Tesseract-OCR\tesseract.exe



Python dependencies
Install all required libraries:

Code:
pip install flask selenium pillow opencv-python numpy pytesseract



2. Running the CAPTCHA Server (Flask)

Step 1: Start the server
Run the Flask app:

Code:
python app.py

Step 2: Access the login page
Open your browser and go to:

Code:
http://localhost:5000/



3. Running the OCR Bot

Step 1: Configure Tesseract path
In the bot script, make sure this line matches your installation:

Code
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


Step 2: Launch the bot
Run the bot script:

Code:
python bot.py


4. Expected Behavior
   
If everything works:
The bot logs in

  Reads the CAPTCHA
  Solves it automatically
  Accesses /nextpage
  Prints the secret message


If the bot fails:
  
  CAPTCHA refreshes
  Bot retries

After 5 failures, the server blocks further attempts



5. Project Structure


/CAPTCHA BREAKER BOT PROJECT
│
├── app.py                
├── bot.py                
├── templates/            
│   ├── login.html
│   ├── user.html
│   └── nextpage.html
├── static/  
|    ├── style.css
|    ├── fonts (arial.ttf) 
