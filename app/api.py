from fastapi import FastAPI, Request, HTTPException, Response
import os
import requests
import httpx
app = FastAPI()

WEBHOOK_VERIFY_TOKEN = os.getenv("WEBHOOK_VERIFY_TOKEN")
GRAPH_API_TOKEN = os.getenv("GRAPH_API_TOKEN")

# Dictionary to store user sessions
user_sessions = {}

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()

    business_phone_number_id = data.get('entry', [{}])[0].get('changes', [{}])[0].get('value', {}).get('metadata', {}).get('phone_number_id')
    user_phone_number = None  # Initialize user_phone_number
    entries = data.get('entry', [])
    if entries:
        changes = entries[0].get('changes', [])
        if changes:
            value = changes[0].get('value', {})
            messages = value.get('messages', [])
            if messages:
                user_phone_number = messages[0].get('from')   

    # Check if the user has an existing session
    if user_phone_number and user_phone_number not in user_sessions:
        user_sessions[user_phone_number] = {
            'current_step': 'start'
        }

    if user_phone_number:
        user_info = user_sessions[user_phone_number]
        current_step = user_info['current_step']

    message = data.get('entry', [{}])[0].get('changes', [{}])[0].get('value', {}).get('messages', [{}])[0]

    if message.get('type') == 'text':
        text = message['text']['body'].lower()
        if text in ['hi', 'hello']:
            send_message(business_phone_number_id, message, "Hello! Welcome to our WhatsApp bot. To stop the conversation, send 'stop'")
            send_button_message(business_phone_number_id, message)
            user_sessions[user_phone_number]['current_step'] = 'button_selected'
        elif text == 'stop':
            send_message(business_phone_number_id, message, "You have successfully stopped the conversation. Send 'hi' to start again.")
            del user_sessions[user_phone_number]
        else:
            send_message(business_phone_number_id, message, "I didn't understand that. Please try again or send 'stop' to end the conversation or Message 'Hi' to start again.")

    elif message.get('type') == 'document':
        if current_step == 'invoice':
           upload_id = await upload_to_tally(message, 'invoice')
           send_message(business_phone_number_id, message, f"{current_step} is the file uploaded. Thank you for uploading. Let me process it {upload_id}.")
           # Process the invoice here
           user_sessions[user_phone_number]['current_step'] = 'start'
        elif current_step == 'receipt':
           upload_id = await upload_to_tally(message, 'invoice')
           send_message(business_phone_number_id, message, f"{current_step} is the file uploaded. Thank you for uploading. Let me process it {upload_id}.")
           # Process the receipt here
           user_sessions[user_phone_number]['current_step'] = 'start'
        else:
           send_message(business_phone_number_id, message, "I received your document. Let me process it.")
           # Process the document here

    elif 'interactive' in message:
        payload = message['interactive']['button_reply']['id']
        if payload == 'INVOICE':
            send_message(business_phone_number_id, message, "Please upload your invoice. File should be in JPG, PNG, PDF.")
            user_sessions[user_phone_number]['current_step'] = 'invoice'
        elif payload == 'RECEIPT':
            send_message(business_phone_number_id, message, "Please upload your receipt. File should be in JPG, PNG, PDF.")
            user_sessions[user_phone_number]['current_step'] = 'receipt'

    return {"status": "success"}



async def upload_to_tally(message, file_type):
    url = "https://040e-175-101-104-21.ngrok-free.app/1/uploads/upload"
    file_data =  message.get('document', {}).get('file')
    file_name = message.get('document', {}).get('file_name', 'document.pdf')  # Use the file name if available, otherwise use a default name
    files = {"file": (file_name, file_data, "application/pdf")}
    data = {
        "file_type": file_type,
        "uuid": "f81d4fae-7dec-11d0-a765-00a0c91e6b78"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, files=files, data=data)
        response.raise_for_status()
        return response.json()["id"]

def send_message(business_phone_number_id, message, text):
    url = f"https://graph.facebook.com/v18.0/{business_phone_number_id}/messages"
    headers = {"Authorization": f"Bearer {GRAPH_API_TOKEN}"}
    data = {
        "messaging_product": "whatsapp",
        "to": message['from'],
        "text": {"body": text}
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
        "type": "interactive",
        "interactive": {
            "type": "button",
            "header": {
                "type": "text",
                "text": "Which documents you need to process?"
            },
            "body": {
                "text": "Please select an option:"
            },
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {
                            "id": "INVOICE",
                            "title": "Invoice"
                        }
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": "RECEIPT",
                            "title": "Receipt"
                        }
                    }
                ]
            }
        }
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code != 200:
        print(f"Error sending message buttons: {response.content}")


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
