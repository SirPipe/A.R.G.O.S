import speech_recognition as sr
import os

r = sr.Recognizer()

while True:
    with sr.Microphone() as source:
        print("Escuchando...")
        audio = r.listen(source)

    try:
        comando = r.recognize_google(audio, language="es-ES").lower()

        print("Dijiste:", comando)

        # YOUTUBE
        if "youtube" in comando:
            os.system("firefox https://youtube.com")

        # WHATSAPP
        elif "whatsapp" in comando:
            os.system("firefox https://web.whatsapp.com")

        # GOOGLE
        elif "google" in comando:
            os.system("firefox https://google.com")

        # TERMINAR
        elif "salir" in comando:
            print("Cerrando Jarvis...")
            break

    except Exception as e:
        print("No entendí:", e)
