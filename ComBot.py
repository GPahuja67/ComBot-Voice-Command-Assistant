import pyttsx3
import tkinter as tk
from tkinter import simpledialog, messagebox
import speech_recognition as sr
import subprocess
import threading
import datetime
import requests
import time
import re

recognizer = sr.Recognizer()
engine = pyttsx3.init()
engine.setProperty('rate', 125)

voices = engine.getProperty('voices')
for voice in voices:
    if 'female' in voice.name.lower():
        engine.setProperty('voice', voice.id)
        break

API_KEY = 'AIzaSyAh-_j0hbE6a1DlzNbUH8_TLAG6-eTq7j0'
CX = '3011e78e9e3b64066'

reminders = []

# Speak function
def speak(text):
    engine.say(text)
    engine.runAndWait()

# Listen function
def listen():
    try:
        mic = sr.Microphone(device_index=1)
        with mic as source:
            status_label.config(text="Listening...")
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
            status_label.config(text="Recognizing...")
            try:
                return recognizer.recognize_google(audio).lower()
            except sr.UnknownValueError:
                return ""
            except sr.RequestError:
                return ""
    except Exception as e:
        print("Mic error:", e)
        return ""

# Google Search
def google_search(query):
    url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={API_KEY}&cx={CX}"
    response = requests.get(url)
    if response.status_code == 200:
        results = response.json().get('items', [])
        if results:
            result = results[0]
            reply = f"Here's the top result: {result['title']}\n{result['snippet']}\nOpening in browser..."
            try:
                subprocess.run(['xdg-open', result['link']], check=True)
            except Exception as e:
                reply += f"\nError opening browser: {e}"
        else:
            reply = "Sorry, no results found."
    else:
        reply = "Search error."

    speak(reply)
    response_box.insert(tk.END, f"ComBot: {reply}\n")

# Reminder check loop
def reminder_loop():
    while True:
        now = datetime.datetime.now().strftime('%H:%M')
        for task, t in reminders:
            if t == now:
                speak(f"Reminder: {task}")
        time.sleep(60)

# GUI input dialog for reminders
def prompt_reminder():
    def set_reminder():
        task = simpledialog.askstring("Set Reminder", "Enter task name:")
        if task:
            minutes = simpledialog.askinteger("Set Reminder", "Remind in how many minutes?")
            if minutes is not None:
                remind_time = (datetime.datetime.now() + datetime.timedelta(minutes=minutes)).strftime('%H:%M')
                reminders.append((task, remind_time))
                messagebox.showinfo("Reminder Set", f"Reminder set for '{task}' at {remind_time}.")
                speak(f"Reminder set for {task} in {minutes} minutes")
            else:
                speak("Reminder time not set.")
        else:
            speak("No task entered.")    
    root.after(100, set_reminder)

# Perform action
def perform_action(command):
    if 'hello' in command:
        reply = "Hello! How can I help you today?"

    elif 'open mozilla' in command:
        subprocess.run(["firefox"])
        reply = "Opening Mozilla Firefox."

    elif 'open settings' in command:
        subprocess.run(["gnome-control-center"])
        reply = "Opening Settings."

    elif 'show date' in command:
        reply = f"The current date is {datetime.datetime.now().strftime('%Y-%m-%d')}"

    elif 'show time' in command:
        reply = f"The current time is {datetime.datetime.now().strftime('%H:%M:%S')}"

    elif 'joke' in command:
        reply = "Why don't programmers like nature? It has too many bugs."

    elif 'search' in command:
        query = command.replace("search", "").strip()
        google_search(query)
        return

    elif 'shutdown in' in command:
        match = re.search(r'shutdown in (\d+)', command)
        if match:
            minutes = int(match.group(1))
            subprocess.run(['shutdown', '-h', f'+{minutes}'])
            reply = f"System will shutdown in {minutes} minutes."
        else:
            reply = "Please say 'shutdown in X minutes'."

    elif 'set reminder' in command:
        prompt_reminder()
        return

    elif 'remind me' in command:
        match = re.search(r'remind me to (.+?) at (\d{1,2}:\d{2})', command)
        if match:
            task, time_str = match.groups()
            reminders.append((task, time_str))
            reply = f"Reminder set for '{task}' at {time_str}."
        else:
            reply = "Please say 'remind me to task at HH:MM'."

    elif 'calculate' in command:
        try:
            expression = command.replace('calculate', '').strip()
            expression = expression.lower()

        # Spoken to math symbol replacements
            expression = expression.replace('plus', '+')
            expression = expression.replace('minus', '-')
            expression = expression.replace('times', '*')
            expression = expression.replace('multiplied by', '*')
            expression = expression.replace('divided by', '/')
            expression = expression.replace('into', '*')
            expression = expression.replace('by', '/')
            expression = expression.replace('x', '*')  # if user says "10 x 2"

        # Remove any unwanted characters
            expression = ''.join(char for char in expression if char in '0123456789+-*/(). ')

            if expression:
                result = eval(expression)
                reply = f"The result is {result}."
            else:
                reply = "Please say a valid calculation."
        except Exception as e:
            reply = f"Error in calculation: {e}"
        
    elif 'exit' in command or 'stop' in command:
        reply = "Goodbye!"
        speak(reply)
        response_box.insert(tk.END, f"ComBot: {reply}\n")
        root.quit()
        return

    else:
        reply = "I didn't understand that command."

    speak(reply)
    response_box.insert(tk.END, f"ComBot: {reply}\n")

# Threaded listening
def start_listening_thread():
    threading.Thread(target=start_listening).start()

def start_listening():
    message_box.delete(1.0, tk.END)
    command = listen()
    if command:
        message_box.insert(tk.END, f"{command}\n")
        perform_action(command)
    else:
        message_box.insert(tk.END, "Could not recognize.\n")
        response_box.insert(tk.END, "ComBot: Could not recognize.\n")

# Help window
def show_help():
    help_win = tk.Toplevel(root)
    help_win.title("ComBot Help")
    help_win.geometry("400x400")
    tk.Label(help_win, text="Supported Commands:", font=("Helvetica", 14, "bold")).pack(pady=10)
    commands = [
        "hello",
        "open mozilla",
        "open settings",
        "show date / show time",
        "joke",
        "search <query>",
        "shutdown in <minutes>",
        "set reminder",
        "remind me to <task> at HH:MM",
        "calculate <expression>",
        "exit / stop"
    ]
    for cmd in commands:
        tk.Label(help_win, text=cmd, font=("Helvetica", 12)).pack(anchor='w', padx=20)

# GUI
root = tk.Tk()
root.title("ComBot - Voice Assistant")
root.geometry("800x1000")
root.configure(bg='#2C3E50')

header = tk.Label(root, text="ComBot - Voice Assistant", font=("Arial", 24, "bold"), fg="white", bg='#2C3E50')
header.pack(pady=12)

info_box = tk.LabelFrame(root, text="Meet ComBot!!", font=("Helvetica", 10), fg="white", bg='#34495E')
info_box.pack(pady=16, padx=12, fill="x")
tk.Label(info_box, text="Meet ComBot – your personal voice assistant!\nAsk it to perform tasks like opening apps, telling the time, or just having a chat",
         bg='#34495E', fg="white", font=("Helvetica", 16)).pack(pady=7)

status_label = tk.Label(root, text="Press 'Start Listening' to talk", font=("Helvetica", 14), fg="white", bg='#2C3E50')
status_label.pack(pady=9)

message_frame = tk.Frame(root, bg='#2C3E50')
message_frame.pack(pady=9, padx=12, fill="x")

message_label = tk.Label(message_frame, text="Your Command:", font=("Helvetica", 12), fg="white", bg='#2C3E50')
message_label.pack(anchor='w')

message_box = tk.Text(message_frame, height=4, font=("Helvetica", 12), wrap=tk.WORD)
message_box.pack(fill="x")

response_frame = tk.Frame(root, bg='#2C3E50')
response_frame.pack(pady=7, padx=12, fill="x")

response_label = tk.Label(response_frame, text="ComBot Response:", font=("Helvetica", 12), fg="white", bg='#2C3E50')
response_label.pack(anchor='w')

response_box = tk.Text(response_frame, height=10, font=("Helvetica", 12), wrap=tk.WORD)
response_box.pack(fill="x")

button_frame = tk.Frame(root, bg='#2C3E50')
button_frame.pack(pady=20)

start_button = tk.Button(button_frame, text="Start Listening", font=("Helvetica", 14), bg="#3498DB", fg="white", command=start_listening_thread)
start_button.grid(row=0, column=0, padx=10)

exit_button = tk.Button(button_frame, text="Exit Chat", font=("Helvetica", 14), bg="#E74C3C", fg="white", command=lambda: (speak("Goodbye!"), root.quit()))
exit_button.grid(row=0, column=2, padx=10)

help_icon = tk.Button(root, text="❓", font=("Helvetica", 16, "bold"), bg="#2C3E50", fg="white", bd=0, command=show_help, cursor="hand2")

help_icon.place(relx=0.97, rely=0.02, anchor="ne")  # Top-right corner

threading.Thread(target=reminder_loop, daemon=True).start()

root.mainloop()
