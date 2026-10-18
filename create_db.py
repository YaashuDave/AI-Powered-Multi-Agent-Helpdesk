# create_db.py

import sqlite3
import pathlib

db_path = pathlib.Path("data/sample_kb.sqlite")
db_path.parent.mkdir(exist_ok=True)

conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute("DROP TABLE IF EXISTS kb")
cur.execute("""
CREATE TABLE kb (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    content TEXT
)
""")

ARTICLES = [
    ("Login Issue", "User cannot log in. Steps: reset password, check email, clear browser cache."),
    ("Payment Failure", "Payment failed. Steps: retry, verify card, update billing address."),
    ("Password Reset", "Forgotten or expired password. Steps: use 'Forgot password', check spam folder for the reset email, choose a password that meets the policy."),
    ("Account Locked", "Account locked after repeated failed sign-in attempts. Steps: wait 15 minutes or ask IT to unlock, then reset password."),
    ("VPN Connection Failure", "VPN will not connect. Steps: check internet connection, restart the VPN client, verify credentials, update the client."),
    ("Email Not Syncing", "Outlook or mobile email not syncing. Steps: check connection, restart the mail app, remove and re-add the account."),
    ("Wi-Fi Connectivity", "Laptop cannot connect to office Wi-Fi network. Steps: forget the network and reconnect, restart the adapter, check for driver updates."),
    ("Printer Not Working", "Printer offline or jobs stuck in queue. Steps: check power and network, clear the print queue, reinstall the printer driver."),
    ("Slow Computer", "Computer running slow. Steps: restart, close unused apps, check disk space, run updates and a malware scan."),
    ("Software Installation Request", "User needs new software installed. Steps: check approved software catalogue, raise a request with manager approval."),
]

cur.executemany("INSERT INTO kb (title, content) VALUES (?, ?)", ARTICLES)

conn.commit()
conn.close()

print("Database created successfully at:", db_path)
