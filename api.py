from fastapi import FastAPI, Request, HTTPException
import os
import requests

app = FastAPI()

WEBHOOK_VERIFY_TOKEN = os.getenv("WEBHOOK_VERIFY_TOKEN")
GRAPH_API_TOKEN = os.getenv("GRAPH_API_TOKEN")

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()

    message = data.get('entry', [{}])[0].get('changes', [{}])[0].get('value', {}).get('messages', [{}])[0]

    if message.get('type') == 'text':
        business_phone_number_id = data.get('entry', [{}])[0].get('changes', [{}])[0].get('value', {}).get('metadata', {}).get('phone_number_id')

        send_message(business_phone_number_id, message)

    return {"status": "success"}

@app.get("/webhook")
async def verify_webhook(mode: str, token: str, challenge: str):
    if mode == 'subscribe' and token == WEBHOOK_VERIFY_TOKEN:
        return {"challenge": challenge}
    else:
        raise HTTPException(status_code=403, detail="Forbidden")

@app.get("/")
async def root():
    return {"message": "Nothing to see here. Checkout README.md to start."}

def send_message(business_phone_number_id, message):
    url = f"https://graph.facebook.com/v18.0/{business_phone_number_id}/messages"
    headers = {"Authorization": f"Bearer {GRAPH_API_TOKEN}"}
    data = {
        "messaging_product": "whatsapp",
        "to": message['from'],
        "text": {"body": "Echo: " + message['text']['body']},
        "context": {
            "message_id": message['id'],
        },
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code != 200:
        print(f"Error sending message: {response.content}")