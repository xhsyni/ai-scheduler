from datetime import datetime
from zoneinfo import ZoneInfo

# Get current time in a specific timezone
now_tokyo = datetime.now(ZoneInfo("Asia/Kuala_Lumpur"))

# Convert an existing aware datetime to another timezone
now_ny = now_tokyo.astimezone(ZoneInfo("America/New_York"))

print(now_tokyo)
print(now_ny)



# import certifi
# from pymongo import MongoClient
# from pymongo.server_api import ServerApi

# uri = "mongodb+srv://scheduler:uuDApFDXh3UKUpJl@production.o9gjahz.mongodb.net/?appName=production"

# # Create a new client and connect to the server
# # tlsCAFile=certifi.where() fixes TLSV1_ALERT_INTERNAL_ERROR on Windows
# client = MongoClient(uri, server_api=ServerApi('1'), tlsCAFile=certifi.where())

# # Send a ping to confirm a successful connection
# try:
#     client.admin.command('ping')
#     print("Pinged your deployment. You successfully connected to MongoDB!")
# except Exception as e:
#     print(e)
