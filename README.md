# CapsuleConnect - Digital Time Capsule Platform

A social web application where users create time-locked digital capsules. Messages, memories, goals, or confessions stay sealed until a future date. When the date arrives, capsules unlock and appear on the friends feed.

---

## Project Description

CapsuleConnect lets users write letters to their future self, store memories, set goals, and send time-locked messages to friends. It is a full-stack web application built using Flask and MySQL with a Bootstrap frontend.

---

## Features

- User registration and login with form validation
- Create time-locked capsules (Letter, Memory, Goal, Confession)
- Capsule categories - Personal, Public, Sent to someone
- Friends feed - see unlocked capsules from connected users
- Send and accept connection requests
- Chat with image upload and scheduled message delivery
- Break reminder after 20 minutes of usage
- Fully responsive Bootstrap layout

---

## Technologies Used

- Frontend - HTML5, Bootstrap 5
- Styling - Custom CSS 
- Behavior - JavaScript, jQuery 3.7
- Backend - Python, Flask
- Templating - Jinja2
- Database - MySQL
- Icons - Font Awesome 6
- Fonts - Google Fonts (Playfair Display, Mulish)

---

## Project Structure

- app.py
- requirements.txt
- README.md
- static/
  - style.css
  - main.js
  - uploads/
- templates/
  - base.html
  - landing.html
  - login.html
  - register.html
  - feed.html
  - dashboard.html
  - create.html
  - success.html
  - view.html
  - chat.html
  - profile.html
  - search.html

---

## Flask Routes

- / - Landing page
- /register - User registration
- /login - User login
- /logout - Logout
- /feed - Main feed
- /dashboard - User dashboard
- /capsule/create - Create capsule form
- /submit - Form submission handler
- /success - Success confirmation page
- /capsule/id - View a capsule
- /chat - Chat list
- /chat/id - Chat with a specific user
- /profile/username - User profile
- /search - Search people

---

## Setup Instructions

**Step 1 - Clone the repository**

```
git clone https://github.com/tanspan/capsuleconnect.git
cd capsuleconnect
```

**Step 2 - Install dependencies**

```
pip install -r requirements.txt
```

**Step 3 - Set up MySQL database**

Open MySQL Command Line Client and run the schema.sql file.

**Step 4 - Configure database credentials**

Open app.py and update line 8 with your MySQL password:

```
DB = {'host':'localhost','user':'root','password':'yourpassword','database':'capsuleconnect'}
```

**Step 5 - Run the application**

```
python app.py
```

**Step 6 - Open in browser**

```
http://127.0.0.1:5000
```

---

## Demo Steps

1. Open the app at http://127.0.0.1:5000
2. Click Get Started and create an account
3. Login with your credentials
4. Click + New Capsule to create your first capsule
5. Set a future unlock date and lock the capsule
6. Go to People tab and search for another user to connect
7. Accept the connection request from the other account
8. Go to Chat and send a message or schedule one
9. Check Dashboard to see all your capsules

---

## Screenshots
<img width="523" height="597" alt="Screenshot 2026-03-21 233931" src="https://github.com/user-attachments/assets/eeed204c-0805-482a-9044-74b4d53c2d4f" />
<img width="1905" height="804" alt="Screenshot 2026-03-21 233941" src="https://github.com/user-attachments/assets/9c8176c6-4952-4fc4-97f3-dd2b92f9c3d2" />
<img width="1869" height="868" alt="Screenshot 2026-03-21 233951" src="https://github.com/user-attachments/assets/a31a219a-8e95-4ef1-a4aa-5771b11436f1" />
<img width="1363" height="880" alt="Screenshot 2026-03-21 234017" src="https://github.com/user-attachments/assets/eccfd5e2-d255-4c5c-8237-ddc440d00249" />
<img width="1906" height="845" alt="Screenshot 2026-03-21 234030" src="https://github.com/user-attachments/assets/5f39cc17-f195-4cf0-9fd1-11852721f103" />



