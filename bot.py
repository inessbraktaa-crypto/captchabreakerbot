from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

import pytesseract
import cv2
import numpy as np

from PIL import Image
import random
import base64
import re
import time
from collections import Counter
import json
from io import BytesIO

# COLORS
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
RESET = "\033[0m"

URL = "http://localhost:5000/login"
USERNAME = "user"
PASSWORD = "test..123"

# Speed
TYPING_DELAY = 0.15  
CLICK_PAUSE = 0.5    # Pause after click
PAGE_WAIT = 1.5      # Wait for page to load

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

options = Options()
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
driver = webdriver.Chrome(options=options)
driver.get(URL)
time.sleep(2)



# Visual effects for the demo 
def init_visuals(driver): # we inject some CSS styles for the visual effects (red circles for clicks, yellow circles for focus) directly into the page using JavaScript. This allows us to create a more engaging demo by visually representing the bot's interactions on the page.
    driver.execute_script("""
        var style = document.createElement('style');
        style.textContent = `
            .visual-click {
                position: fixed !important;
                width: 50px !important;
                height: 50px !important;
                border-radius: 50% !important;
                background: radial-gradient(circle, rgba(255,0,0,0.95), rgba(255,0,0,0)) !important;
                pointer-events: none !important;
                z-index: 999999 !important;
                animation: fadeOutAnim 0.5s ease-out forwards !important;
            } 
            .visual-focus {
                position: fixed !important;
                width: 70px !important;
                height: 70px !important;
                border-radius: 50% !important;
                background: radial-gradient(circle, rgba(255,255,0,0.85), rgba(255,255,0,0)) !important;
                pointer-events: none !important;
                z-index: 999998 !important;
                animation: fadeOutAnim 0.5s ease-out forwards !important;
            }
            @keyframes fadeOutAnim {
                0% {
                    opacity: 1;
                    transform: scale(0.2);
                }
                100% {
                    opacity: 0;
                    transform: scale(2);
                }
            }
        `;
        document.head.appendChild(style);
    """) # defining red for clicks, yellow for focus (with a fade-out animation) 

def show_red_point(driver, x, y): # we create a red circle at the click position to visualize the click action
    driver.execute_script("""
        var div = document.createElement('div');
        div.className = 'visual-click';
        div.style.left = (arguments[0] - 25) + 'px';
        div.style.top = (arguments[1] - 25) + 'px';
        document.body.appendChild(div);
        setTimeout(function() { if(div && div.remove) div.remove(); }, 500);
    """, x, y) # we position the circle centered on the click coordinates, and we remove it after 500ms to create a fading effect

def show_yellow_point(driver, x, y):
    driver.execute_script("""
        var div = document.createElement('div');
        div.className = 'visual-focus';
        div.style.left = (arguments[0] - 35) + 'px';
        div.style.top = (arguments[1] - 35) + 'px';
        document.body.appendChild(div);
        setTimeout(function() { if(div && div.remove) div.remove(); }, 500);
    """, x, y) # we create a yellow circle at the focus position to visualize the focus action, with the same fade-out effect as clicks but slightly larger and centered on the focus coordinates
 
def click_with_effect(driver, element, description=""): # when we click on an element, we first get its coordinates with JavaScript, then we show a red point at that position to visualize the click, and finally we perform the click action with JavaScrript
    coords = driver.execute_script("""
        var rect = arguments[0].getBoundingClientRect();
        return { x: rect.left + rect.width/2 + window.scrollX, y: rect.top + rect.height/2 + window.scrollY };
    """, element) # we calculate the center coordinates of the element by getting its bounding rectangle and adding the current scroll position to account for any scrolling on the page
    show_red_point(driver, coords['x'], coords['y']) # after showing the red point to visualize the click, we perform the actual click action using JavaScript to ensure it works even if the element is not interactable in the traditional way (e.g., due to overlays or other issues). We also add a small pause after the click to allow any resulting actions to take effect before proceeding
    time.sleep(0.1)
    driver.execute_script("arguments[0].click();", element) #
    time.sleep(CLICK_PAUSE)

def focus_with_effect(driver, element, description=""): # when we focus on an element, we get its coordinates and show a yellow point to visualize the focus action, then we perform the focus action with JavaScript. This is useful to simulate more human-like interactions and to visualize where the bot is focusing on the page
    coords = driver.execute_script("""
        var rect = arguments[0].getBoundingClientRect();
        return { x: rect.left + rect.width/2 + window.scrollX, y: rect.top + rect.height/2 + window.scrollY };
    """, element) # 
    show_yellow_point(driver, coords['x'], coords['y'])
    driver.execute_script("arguments[0].focus();", element)
    time.sleep(0.15) 

def type_text(element, text, description=""):  # delay between keystrokes to simulate human typing, and we print the characters being typed for the demo
    if description:
        print(f"Typing: {description}")
    for i, char in enumerate(text):
        element.send_keys(char)
        print(f" → '{char}'")
        time.sleep(TYPING_DELAY) # see in logs the characters being typed one by one with a delay to simulate human typing speed



# FAKE BEHAVIOR DATA TO BYPASS BOT DETECTION
def generate_behavior_data():
    behavior = {
        "velocities": [random.uniform(0.5, 2.5) for _ in range(random.randint(30, 50))],
        "dir_changes": random.randint(5, 20),
        "straight": random.randint(1, 8),
        "event_count": random.randint(30, 50)
    }
    return behavior

def inject_behavior_data(driver, behavior_data): # we inject the generated behavior data into the page by creating a hidden input field with JavaScript and appending it to the form. This attack is called data injection
    try:
        driver.execute_script("""
            var oldInput = document.querySelector('input[name="bot_behavior"]');
            if (oldInput) oldInput.remove();
            var input = document.createElement('input');
            input.type = 'hidden';
            input.name = 'bot_behavior';
            input.value = arguments[0];
            var form = document.querySelector('form');
            if (form) form.appendChild(input);
        """, json.dumps(behavior_data))  # we first check if there is already an input field with the name "bot_behavior" and remove it to avoid duplicates, then we create a new hidden input field, set its value to the JSON string of the behavior data, and append it to the form on the page. This way, when the form is submitted, the server will receive this injected behavior data along with the other form data, which can help bypass bot detection mechanisms that rely on analyzing user behavior patterns. We wrap this in a try-except block to avoid any potential errors if the form or input field cannot be created for some reason.
    except:
        pass

# CAPTCHA OCR 
def get_captcha_image():
    try:
        # wait for the captcha image to be present
        captcha_img = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "captchaImage")))
        
        for _ in range(10):  # try up to 10 times to ensure the image is loaded
            is_loaded = driver.execute_script("""
                var img = arguments[0];
                return img.complete && img.naturalWidth > 0 && img.naturalHeight > 0;
            """, captcha_img)
        
            if is_loaded:
                break
            time.sleep(0.5)  # wait a bit before checking again
        else:
            print(RED + "Captcha image not loaded yet, retrying..." + RESET)    
            return None  # if the image is still not loaded after 10 tries, return None to indicate failure    
        


        img_b64 = driver.execute_script("""
            var img = document.getElementById('captchaImage');
            if (!img) return null;
            if (!img.complete || img.naturalWidth === 0) return null;
            var canvas = document.createElement('canvas');
            canvas.width = img.naturalWidth || img.width;
            canvas.height = img.naturalHeight || img.height;
            var ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
            return canvas.toDataURL('image/png').split(',')[1];
        """) # with js we get the captcha image as a base64 string, we check if the image is loaded and valid before trying to read it. If it's not ready, we return null to avoid errors.
    
        if img_b64:
            img_data = base64.b64decode(img_b64) # we decode the base64 string to get the binary image data, then we create a PIL Image object from it to process with OCR. If the image is not available or valid, we return None.
            return Image.open(BytesIO(img_data)) # we return the PIL Image object to be processed by the OCR function. If there was an issue with loading the image, we return None to indicate failure.
        else:
            print(RED + "Captcha image not available or not loaded yet." + RESET)
            return None
        
    except Exception as e:
        print(RED + f"Error getting captcha image: {e}" + RESET)
        return None


def ocr_captcha():
    img = get_captcha_image()
    if img is None:
        print(RED + "Failed to get captcha image" + RESET)
        return ""

    img_array = np.array(img) # we convert the PIL Image to a NumPy array for processing with OpenCV, which is more efficient for image manipulation. This allows us to apply various preprocessing techniques to enhance the image before performing OCR, such as noise reduction, thresholding, and morphological operations. If the image could not be loaded, we return an empty string to indicate failure.
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY) # we convert the image to grayscale to simplify the processing and improve OCR accuracy, as color information is not necessary for recognizing the characters in the captcha. This also helps to reduce noise and focus on the shapes of the characters. If the image could not be loaded, we return an empty string to indicate failure.

    candidates = []
    preprocessed_versions = []

    # Remove lines 
    kernel_h = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1)) #it creates a horizontal structuring element (a rectangular kernel) that is 25 pixels wide and 1 pixel tall. This kernel is used for morphological operations to detect and remove horizontal lines from the image, which can interfere with OCR accuracy. By applying a morphological opening operation with this kernel, we can isolate and remove horizontal lines while preserving the characters in the captcha. We do the same with a vertical kernel to remove vertical lines, which are also common in captcha images to add noise and make OCR more difficult.
    kernel_v = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 25)) # same vertical kernel to remove vertical lines
    lines_h = cv2.morphologyEx(gray, cv2.MORPH_OPEN, kernel_h) # we apply a morphological opening operation to the grayscale image using the horizontal kernel to detect and isolate horizontal lines. This operation will help to remove these lines from the image, which can improve OCR accuracy by reducing noise and making the characters more distinct. We do the same with the vertical kernel to remove vertical lines, which can also interfere with OCR accuracy.
    lines_v = cv2.morphologyEx(gray, cv2.MORPH_OPEN, kernel_v)
    lines_mask = cv2.add(lines_h, lines_v) # we combine the detected horizontal and vertical lines into a single mask, which we can then subtract from the original grayscale image to remove these lines. This helps to clean up the image and enhance the visibility of the characters for OCR processing. By removing these lines, we can improve the chances of accurately recognizing the characters in the captcha, as they will be less obscured by noise.
    cleaned = cv2.subtract(gray, lines_mask) # we subtract the combined lines mask from the original grayscale image to remove the detected horizontal and vertical lines. This results in a cleaner image with less noise, which can improve OCR accuracy by making the characters more distinct and easier to recognize. By removing these lines, we can enhance the visibility of the characters in the captcha, increasing the chances of successfully solving it with OCR. We add this cleaned version to our list of preprocessed versions to test with OCR, as different preprocessing techniques can yield better results depending on the specific captcha image.
    preprocessed_versions.append(cv2.threshold(cleaned, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]) # we apply Otsu's thresholding to the cleaned image to convert it to a binary image, which can further enhance the contrast between the characters and the background. This can improve OCR accuracy by making the characters more distinct and easier to recognize. We add this preprocessed version to our list of versions to test with OCR, as different preprocessing techniques can yield better results depending on the specific captcha image.

    # OTSU thresholding
    _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    preprocessed_versions.append(otsu)

    # Threshold to keep only dark areas (the letters) to improve OCR accuracy by reducing noise and focusing on the characters, which are typically darker than the background in captcha images. By applying a binary threshold that keeps only the dark areas, we can enhance the visibility of the characters and make them more distinct for OCR processing. We add this preprocessed version to our list of versions to test with OCR, as different preprocessing techniques can yield better results depending on the specific captcha image.
    _, dark_only = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY)
    preprocessed_versions.append(dark_only)

    # HSV to isolate colored letters (hsv means hue, saturation, value - it's a color space that can be useful to isolate certain colors based on their hue and saturation, which can help to enhance the characters in the captcha if they are colored differently from the background. By converting the image to HSV color space and applying a threshold to isolate the saturation channel, we can create a mask that highlights the characters while suppressing the background. This can improve OCR accuracy by making the characters more distinct and easier to recognize. We add this preprocessed version to our list of versions to test with OCR, as different preprocessing techniques can yield better results depending on the specific captcha image.)
    img_array_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    hsv = cv2.cvtColor(img_array_bgr, cv2.COLOR_BGR2HSV) # we convert the original image from RGB to BGR color space, which is the default color format used by OpenCV. This allows us to then convert it to HSV color space, which can be useful for isolating certain colors based on their hue and saturation. By working in HSV color space, we can apply thresholds to isolate the characters in the captcha if they are colored differently from the background, which can enhance OCR accuracy by making the characters more distinct and easier to recognize. We add this preprocessed version to our list of versions to test with OCR, as different preprocessing techniques can yield better results depending on the specific captcha image.
    sat = hsv[:, :, 1] # we extract the saturation channel from the HSV image, which can help to isolate the characters in the captcha if they have a different saturation level than the background. By applying a threshold to the saturation channel, we can create a mask that highlights the characters while suppressing the background, which can improve OCR accuracy by making the characters more distinct and easier to recognize. We add this preprocessed version to our list of versions to test with OCR, as different preprocessing techniques can yield better results depending on the specific captcha image.
    _, sat_mask = cv2.threshold(sat, 40, 255, cv2.THRESH_BINARY)
    combined = cv2.bitwise_or(sat_mask, cv2.threshold(gray, 0, 100, cv2.THRESH_BINARY_INV)[1])
    preprocessed_versions.append(combined) # we combine the saturation mask with an inverse threshold of the grayscale image to create a new preprocessed version that can enhance the visibility of the characters in the captcha. By combining these two masks, we can capture both the color information from the saturation channel and the intensity information from the grayscale image, which can improve OCR accuracy by making the characters more distinct and easier to recognize. We add this combined version to our list of versions to test with OCR, as different preprocessing techniques can yield better results depending on the specific captcha image.

    # Sharpening
    sharp_kernel = np.array([[-1,-1,-1],[-1,9,-1],[-1,-1,-1]]) # this helps to improve the contrast and make the characters more distinct for OCR processing. By applying a sharpening filter to the grayscale image, we can enhance the edges and details of the characters in the captcha, which can improve OCR accuracy by making them more recognizable. We add this preprocessed version to our list of versions to test with OCR, as different preprocessing techniques can yield better results depending on the specific captcha image.
    sharpened = cv2.filter2D(gray, -1, sharp_kernel) # we apply the sharpening filter to the grayscale image using the defined kernel, which can enhance the edges and details of the characters in the captcha. This can improve OCR accuracy by making the characters more distinct and easier to recognize. We add this preprocessed version to our list of versions to test with OCR, as different preprocessing techniques can yield better results depending on the specific captcha image.
    preprocessed_versions.append(cv2.threshold(sharpened, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]) 

    # Denoising
    denoised = cv2.fastNlMeansDenoising(gray, h=15) # we apply a denoising filter to the grayscale image to reduce noise and improve OCR accuracy. By using the Non-Local Means Denoising algorithm, we can effectively remove noise while preserving the edges and details of the characters in the captcha. This can enhance the visibility of the characters and make them more distinct for OCR processing. We add this preprocessed version to our list of versions to test with OCR, as different preprocessing techniques can yield better results depending on the specific captcha image. (the algorithm is taken from opencv)
    preprocessed_versions.append(cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1])




    configs = [
    "--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",  # ligne de texte
    "--psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",  # mot
    "--psm 13 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", # ligne brute
    ] # we define different Tesseract configurations to test with OCR, using different page segmentation modes (PSM) and whitelisting only uppercase letters and digits, which are the expected characters in the captcha. By testing multiple configurations, we can increase the chances of successfully recognizing the characters in the captcha, as different configurations may yield better results depending on the specific image and its characteristics.


    for processed in preprocessed_versions:
        for scale in [2, 3, 4, 5]: # for each version we create multiple scaled versions to improve OCR accuracy
            resized = cv2.resize(processed, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
            for config in configs:
                text = pytesseract.image_to_string(resized, config=config).strip() # we use Tesseract OCR to extract text from the preprocessed and scaled images, testing with different configurations to improve accuracy. We strip the resulting text to remove any leading or trailing whitespace, and then we clean it by removing any characters that are not uppercase letters or digits, which are the expected characters in the captcha. If the cleaned text has a length of 5 (the expected length of the captcha), we add it to our list of candidates for the final result. By testing multiple preprocessing techniques, scales, and OCR configurations, we can increase the chances of successfully recognizing the characters in the captcha and solving it.
                text = re.sub(r"[^A-Z0-9]", "", text) # we clean the OCR result by removing any characters that are not uppercase letters or digits   
                if len(text) == 5:
                    candidates.append(text)

    if not candidates:
        return ""

    most_common = Counter(candidates).most_common(1)[0][0] # we use a Counter to find the most common OCR result among the candidates, which can help to improve accuracy by selecting the result that appears most frequently across different preprocessing techniques, scales, and OCR configurations. This can help to mitigate errors from individual OCR attempts and increase the chances of correctly solving the captcha. We print the candidates and the final chosen result for the demo, to show how the bot is processing the captcha image and making its decision based on multiple attempts.
    print(CYAN + f"Candidates: {Counter(candidates)}" + RESET) 
    return most_common


# activate visuals for the demo
init_visuals(driver)


# LOGIN 
print(YELLOW + "Logging in..." + RESET)

inject_behavior_data(driver, generate_behavior_data()) # we inject some behavior data on login to avoid instant bot detection

username_field = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "username")))
focus_with_effect(driver, username_field, "username field")
type_text(username_field, USERNAME, "username")

password_field = driver.find_element(By.NAME, "password")
focus_with_effect(driver, password_field, "password field")
type_text(password_field, PASSWORD, "password")

submit_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
click_with_effect(driver, submit_btn, "login submit button")
time.sleep(PAGE_WAIT)

if "/user" not in driver.current_url:
    print(RED + "Login failed!" + RESET)
    driver.quit()
    exit()

print(GREEN + "Login successful!\n" + RESET)



# CAPTCHA MAIN LOOP 
MAX_ATTEMPTS = 5

for attempt in range(1, MAX_ATTEMPTS + 1):
    print(YELLOW + f"Attempt {attempt}/{MAX_ATTEMPTS}..." + RESET)
    
    if "/login" in driver.current_url:
        inject_behavior_data(driver, generate_behavior_data()) 
        
        username_field = driver.find_element(By.NAME, "username")
        focus_with_effect(driver, username_field, "username field")
        type_text(username_field, USERNAME, "username")
        
        password_field = driver.find_element(By.NAME, "password")
        focus_with_effect(driver, password_field, "password field")
        type_text(password_field, PASSWORD, "password")
        
        click_with_effect(driver, driver.find_element(By.CSS_SELECTOR, "button[type='submit']"), "login button")
        time.sleep(PAGE_WAIT)
        continue
    
    inject_behavior_data(driver, generate_behavior_data()) 


    
    # Show captcha image load
    print("Reading captcha image...")
    captcha_text = ocr_captcha()
    print(CYAN + f"OCR result: '{captcha_text}'" + RESET)
    
    if len(captcha_text) != 5:
        print(RED + "Bad OCR length, refreshing..." + RESET)
        try:
            refresh_btn = driver.find_element(By.CLASS_NAME, "buttonrefresh")
            click_with_effect(driver, refresh_btn, "refresh button")
        except:
            driver.refresh()
        time.sleep(1.5)
        continue
    

    
# Focus and type captcha
    captcha_input = driver.find_element(By.NAME, "captcha_input") 
    focus_with_effect(driver, captcha_input, "captcha input field")
    click_with_effect(driver, captcha_input, "captcha input field")
    type_text(captcha_input, captcha_text, "captcha code")
    
    time.sleep(3)
    
    submit = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    click_with_effect(driver, submit, "captcha submit button")
    time.sleep(PAGE_WAIT)
    
    if "/nextpage" in driver.current_url:
        print(GREEN + "CAPTCHA solved!\n" + RESET)
        break
    else:
        print(RED + "Failed, retrying...\n" + RESET)

# SECRET 
try:
    secret = driver.find_element(By.ID, "secretInfo").text
    print(GREEN + f"Secret found: {secret}" + RESET)
except:
    print(RED + "Secret not found" + RESET)

print(YELLOW + "\nBot finished. Closing in 10 seconds..." + RESET)
time.sleep(10)
driver.quit()
