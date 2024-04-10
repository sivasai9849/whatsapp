from fastapi import FastAPI, Request
import os
import requests
from starlette.concurrency import run_in_threadpool

app = FastAPI()

whatsapp_cloud_api_access_token=os.environ.get("WHATSAPP_ACCESS_TOKEN")
sender_phone_number_id=os.environ.get("WHATSAPP_PHONE_NUMBER_ID")

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    await run_in_threadpool(process_message, data)
    return {"status": "success"}

def process_message(message_data):
    from_number = message_data["entry"][0]["changes"][0]["value"]["messages"][0]["from"]

    send_message(from_number, "Your message has been received and stored!")

def send_message(to, body):
    url =  "https://graph.facebook.com/v18.0//messages"
    headers = {"Authorization": f"Bearer {whatsapp_cloud_api_access_token}"}
    data = {
        "to": to,
        "body": body,
        "sender_phone_number_id": sender_phone_number_id,
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code != 200:
        print(f"Error sending message: {response.content}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)