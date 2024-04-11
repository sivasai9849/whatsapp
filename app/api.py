from fastapi import FastAPI, Request, HTTPException, Response
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

        if message['text']['body'].lower() in ['hi', 'hello']:
            send_greeting_message(business_phone_number_id, message)
            send_button_message(business_phone_number_id, message)
        elif message['text']['body'].lower() == 'stop':
            # Handle stop command
            pass
        else:
            # Handle other text messages
            pass
    if message.get('type') == 'image':
        # Handle image messages
        pass

    return {"status": "success"}

def send_greeting_message(business_phone_number_id, message):
    url = f"https://graph.facebook.com/v18.0/{business_phone_number_id}/messages"
    headers = {"Authorization": f"Bearer {GRAPH_API_TOKEN}"}
    data = {
        "messaging_product": "whatsapp",
        "to": message['from'],
        "text": "Hello! I'm here to help you. Send 'stop' to stop the conversation."
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code != 200:
        print(f"Error sending message: {response.content}")

def send_button_message(business_phone_number_id, message):
    url = f"https://graph.facebook.com/v18.0/{business_phone_number_id}/messages"
    headers = {"Authorization": f"Bearer {GRAPH_API_TOKEN}"}
    data = {
        "messaging_product": "whatsapp",
        "to": message['from'],
        "template": {
            "name": "template_name",  # Replace with your template name
            "language": {
                "policy": "deterministic",
                "code": "en_US"
            },
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {
                            "type": "text",
                            "text": "Which documents you need to process?"
                        }
                    ]
                },
                {
                    "type": "button",
                    "sub_type": "quick_reply",
                    "index": "1",
                    "parameters": [
                        {
                            "type": "payload",
                            "payload": "INVOICE"
                        },
                        {
                            "type": "text",
                            "text": "Invoice"
                        }
                    ]
                },
                {
                    "type": "button",
                    "sub_type": "quick_reply",
                    "index": "2",
                    "parameters": [
                        {
                            "type": "payload",
                            "payload": "RECEIPT"
                        },
                        {
                            "type": "text",
                            "text": "Receipt"
                        }
                    ]
                }
            ]
        }
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code != 200:
        print(f"Error sending message: {response.content}")

@app.get("/webhook")
async def verify_webhook(request: Request):
    mode = request.query_params.get('hub.mode')
    token = request.query_params.get('hub.verify_token')
    challenge = request.query_params.get('hub.challenge')
    if mode == 'subscribe' and token == WEBHOOK_VERIFY_TOKEN:
        return Response(content=challenge)
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