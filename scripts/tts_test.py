import objc
import pyttsx3

engine = pyttsx3.init()
engine.say("Hello from pyttsx3 with objc!")
engine.runAndWait()