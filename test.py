import speech_recognition as sr

r = sr.Recognizer()

with sr.Microphone() as source:
    print("Habla...")
    audio = r.listen(source)

try:
    text = r.recognize_google(audio, language="es-ES")
    print("Dijiste:", text)
except:
    print("No entendí")
