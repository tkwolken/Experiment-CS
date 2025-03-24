import os
import sqlite3
import tkinter as tk
from tkinter import messagebox, filedialog
from cryptography.fernet import Fernet
import time
import psutil
import csv

# 🔹 Generiere einen Schlüssel zur Verschlüsselung (einmalig ausführen und speichern)
KEY_FILE = "key.key"

def generate_key():
    """Generiert einen Schlüssel für die Verschlüsselung"""
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as key_file:
            key_file.write(key)

def load_key():
    """Lädt den gespeicherten Schlüssel"""
    with open(KEY_FILE, "rb") as key_file:
        return key_file.read()

# 🔹 Initialisiere Verschlüsselung
generate_key()
cipher = Fernet(load_key())

# 🔹 Datenbank-Verwaltung
DB_FILE = "passwords.db"

def init_db():
    """Erstellt die Passwort-Datenbank, falls sie nicht existiert"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS passwords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service TEXT NOT NULL,
            username TEXT NOT NULL,
            password TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def add_password(service, username, password):
    """Fügt ein verschlüsseltes Passwort zur Datenbank hinzu"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    encrypted_password = cipher.encrypt(password.encode())
    cursor.execute("INSERT INTO passwords (service, username, password) VALUES (?, ?, ?)", 
                   (service, username, encrypted_password))
    conn.commit()
    conn.close()

def get_passwords():
    """Liest die gespeicherten Passwörter aus"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT service, username, password FROM passwords")
    data = cursor.fetchall()
    conn.close()
    return [(service, username, cipher.decrypt(password).decode()) for service, username, password in data]

# 🔹 CSV Export-Funktion
def export_to_csv():
    """Exportiert Passwörter in eine CSV-Datei"""
    passwords = get_passwords()
    if not passwords:
        messagebox.showinfo("Passwort-Manager", "Keine gespeicherten Passwörter gefunden.")
        return
    
    # Öffne Dialog zum Speichern der CSV-Datei
    file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV-Dateien", "*.csv")])
    if file_path:
        try:
            with open(file_path, mode="w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["Service", "Username", "Password"])
                for service, username, password in passwords:
                    writer.writerow([service, username, password])
            messagebox.showinfo("Passwort-Manager", f"Passwörter erfolgreich exportiert nach {file_path}")
        except Exception as e:
            messagebox.showerror("Fehler", f"Beim Exportieren ist ein Fehler aufgetreten: {e}")

# 🔹 GUI mit Tkinter
def show_passwords():
    """Zeigt gespeicherte Passwörter in einem Fenster"""
    passwords = get_passwords()
    
    if not passwords:
        messagebox.showinfo("Passwort-Manager", "Keine gespeicherten Passwörter gefunden.")
        return
    
    window = tk.Tk()
    window.title("Passwort-Manager")
    
    # Anzeige der Passwörter
    for i, (service, username, password) in enumerate(passwords):
        tk.Label(window, text=f"{service} - {username}: {password}").grid(row=i, column=0)

    # Button zum Exportieren der Passwörter als CSV
    export_button = tk.Button(window, text="Passwörter exportieren", command=export_to_csv)
    export_button.grid(row=len(passwords), column=0, pady=10)
    
    window.mainloop()

# 🔹 USB-Erkennung
def check_usb():
    """Überprüft, ob der USB-Stick angeschlossen ist"""
    while True:
        drives = [disk.device for disk in psutil.disk_partitions() if "removable" in disk.opts]
        if drives:
            print(f"USB erkannt: {drives[0]}")
            show_passwords()
            break
        time.sleep(2)

# 🔹 Initialisierung
if __name__ == "__main__":
    init_db()
    check_usb()
