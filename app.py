import random
import string
import time
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from flask import Flask, render_template, request, redirect, session, send_file
import json

from typer import clear

app = Flask(__name__)
app.secret_key = "test..123"  



# Generate a text for the captcha

def generate_captcha_text(length=5):
    letters = string.ascii_uppercase + string.digits # uppercase letters and digits 
    return ''.join(random.choice(letters) for _ in range(length)) 


# Captcha image generation 
@app.route("/captcha")
def captcha():
    # Generate text
    text = generate_captcha_text()
    session["captcha_text"] = text  # we store the text
    session["captcha_time"] = time.time()  # we store the time

    # Create a white image
    width = 260
    height = 90
    image = Image.new("RGB",(width, height),color=(255, 255, 255))

    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype("arial.ttf", 32)


    # Lines between letters 
    for _ in range(5):
        draw.line([random.randint(0, width), random.randint(0, height), random.randint(0, width), random.randint(0, height)], fill=(random.randint(160, 210), random.randint(160, 210), random.randint(160, 210)), width=1)

    # Letters with individual rotation  
    x = 15 # starting x position
    for char in text:
        color = (random.randint(10, 80), random.randint(10, 80), random.randint(10, 80))   # we want dark colors for the letters, to contrast with the white background and the light lines
        char_img = Image.new("RGBA", (55, 65), (0, 0, 0, 0))    # we create a separate image for each character, to rotate it individually without affecting the others
        char_draw = ImageDraw.Draw(char_img) # we draw the character on its separate image
        char_draw.text((5, 5), char, font=font, fill=color + (255,)) # we add full opacity to the color (RGBA) for the character
        rotated = char_img.rotate(random.randint(-25, 25), expand=True, resample=Image.BICUBIC) # we rotate the character randomly between -25 and 25 degrees
        y = random.randint(10, 22) # we randomize the y position of each character to make it more difficult for bots
        image.paste(rotated, (x, y), rotated) # we paste the rotated character on the main image, using itself as a mask to keep transparency
        x += random.randint(32, 42) # we randomize the spacing between characters to make it more difficult for bots


# dots to add noise
    for _ in range(60):
        draw.point((random.randint(0, width - 1), random.randint(0, height - 1)),fill=(random.randint(120, 200), random.randint(120, 200), random.randint(120, 200)))


# light distorsion
    data = (1, random.uniform(-0.06, 0.06), 0, random.uniform(-0.06, 0.06), 1, 0, 0.0002, 0.0002)
    image = image.transform((width, height), Image.PERSPECTIVE, data, Image.BICUBIC)


    # Convert to sendable image
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)

    return send_file(buffer, mimetype="image/png")




# Verify the captcha input
@app.route("/nextpage")
def next_page():
    return render_template("nextpage.html")





# BOT DETECTOR
def _std_dev(values): 
    if len(values) < 2: # if we have less than 2 values, we cannot calculate a standard deviation, so we return 0 (no variability)
        return 0.0
    mean = sum(values) / len(values) # we calculate the mean of the values
    return (sum((v - mean) ** 2 for v in values) / len(values)) ** 0.5 # we calculate the standard deviation using the formula: sqrt(sum((x - mean)^2) / n)
 
 
def analyze_bot_score(behavior: dict) -> int:

    velocities  = behavior.get("velocities", []) # list of time intervals between keystrokes or mouse movements
    dir_changes = int(behavior.get("dir_changes", 0)) # number of times the user changed direction in mouse movement
    straight    = int(behavior.get("straight", 0)) # number of times the user moved in a straight line for more than 3 consecutive movements
    event_count = int(behavior.get("event_count", 0)) # total number of keystrokes and mouse movements recorded

    if len(velocities) < 10:
        # Not enough data – treat as neutral (no penalty, no bonus)
        return 85
 
    avg_vel = sum(velocities) / len(velocities) # we calculate the average velocity of the user's interactions (keystrokes and mouse movements)
    std     = _std_dev(velocities) # we calculate the standard deviation of the velocities to measure how consistent the user's interactions are
    rel_std = std / avg_vel if avg_vel > 0 else 0 # we calculate the relative standard deviation to normalize it by the average velocity, so we can compare users with different speeds
 
    score = 0
 
    if rel_std < 0.08:                          # velocity almost constant
        score += 30
    if straight > 3:                            # too many straight lines
        score += 25
    if dir_changes < 2 and len(velocities) > 20:  # robot goes straight
        score += 20
    if avg_vel > 5 and rel_std < 0.15:          # fast & perfectly steady
        score += 15
    if event_count < 10 and len(velocities) > 15:  # sparse events
        score += 10
 
    return min(score, 100)
 









@app.route("/verify", methods=["POST"])
def verify():

    session["captcha_attempts"] = session.get("captcha_attempts", 0) + 1

    if session["captcha_attempts"] > 5:
        session.clear()
        return redirect("/login?error=Too many CAPTCHA attempts")
    




# BOT DETECTION
    raw=request.form.get("bot_behavior", "{}") 
    try:
        behavior = json.loads(raw)
        behavior["velocities"] = [float(v)
for v in behavior.get("velocities", [])] # we convert velocities to floats
    except (ValueError, TypeError):
        behavior = {} 

    bot_score = analyze_bot_score(behavior)
    if bot_score >= 65:
        session.clear()
        return redirect("/login?error=Bot-like behavior detected (score: {bot_score}), access denied.")




    user_input = request.form.get("captcha_input")
    real_text = session.get("captcha_text")
    creation_time = session.get("captcha_time")

    # Expiration after 30 seconds
    if creation_time and time.time() - creation_time > 30:
        return render_template("user.html", error="CAPTCHA expired, please try again.")

    if user_input and user_input.upper() == real_text:
        session["captcha_attempts"] = 0
        return redirect("/nextpage")
    else:
        return render_template("user.html", error="Incorrect CAPTCHA, try again.")


# login and pages
@app.route("/")
def home():
    return redirect("/login")

@app.route("/login", methods=["GET"])
def login_page():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login_action():
    username = request.form.get("username")
    password = request.form.get("password")

  
    if username == "admin" and password == "test..123":
        session["role"] = "admin"
        return redirect("/admin")

    if username == "user" and password == "test..123":
        session["role"] = "user"
        return redirect("/user")

    return "incorrect login or password"

@app.route("/user")
def user_page():
    if session.get("role") != "user":
        return redirect("/login")
    return render_template("user.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")
    



# run flask app
if __name__ == "__main__":
    app.run(debug=True)
