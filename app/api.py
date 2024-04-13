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
    business_phone_number_id = data.get('entry', [{}])[0].get('changes', [{}])[0].get('value', {}).get('metadata', {}).get('phone_number_id')

    if message.get('type') == 'text':
        text = message['text']['body'].lower()
        if text in ['hi', 'hello']:
            send_message(business_phone_number_id, message, "Hello! Welcome to our WhatsApp bot. To stop the conversation, send 'stop'")
            send_button_message(business_phone_number_id, message)
        elif text == 'stop':
            send_message(business_phone_number_id, message, "You have successfully stopped the conversation. Send 'hi' to start again.")
        else:
            send_message(business_phone_number_id, message, "I didn't understand that. Please try again or send 'stop' to end the conversation or Message 'Hi' to start again.")

    elif message.get('type') == 'image':
        send_message(business_phone_number_id, message, "I received your image. Let me process it.")
        response=upload_document(business_phone_number_id, message, 'image')
        if response.status_code == 200:
            invoices = response.json()
            send_message(business_phone_number_id, message, f"Here are the invoices: {invoices['invoices'][0]}")
        else:
            send_message(business_phone_number_id, message, "Error fetching invoices.")
    elif message.get('type') == 'document':
        send_message(business_phone_number_id, message, "I received your document. Let me process it.")
        response=upload_document(business_phone_number_id, message, 'document')
        if response.status_code == 200:
            invoices = response.json()
            send_message(business_phone_number_id, message, f"Here are the invoices: {invoices['invoices'][0]}")
        else:
            send_message(business_phone_number_id, message, "Error fetching invoices.")
            
    elif 'interactive' in message:
        payload = message['interactive']['button_reply']['id']
        if payload == 'INVOICE':
            send_message(business_phone_number_id, message, "Please upload your invoice.File should be in JPG, PNG, PDF.")
        elif payload == 'RECEIPT':
            send_message(business_phone_number_id, message, "Please upload your receipt.File should be in JPG, PNG, PDF.")    
    return {"status": "success"}

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

def upload_document(business_phone_number_id, message, document_type):
    if document_type == 'image':
        file_type = 'receipt'
    elif document_type == 'document':
        file_type = 'invoice'
    else:
        return

    url = f"https://111f-2401-4900-6572-21b8-a5f3-7e7d-e71f-ebc2.ngrok-free.app/1/uploads/upload"
    files = {
        'file_type': (None, file_type),
        'file': (f"{message['id']}.jpg", message['data'], 'image/jpeg'),
        'uuid': (None, 'f81d4fae-7dec-11d0-a765-00a0c91e6b78')
    }
    response = requests.post(url, files=files)
    if response.status_code == 200:
        send_message(business_phone_number_id, message, "Thank you, I have received your document and I am processing it.")
    else:
        send_message(business_phone_number_id, message, "There was an error uploading your document. Please try again.")
    
    return response    

# def send_message(business_phone_number_id, message):
#     url = f"https://graph.facebook.com/v18.0/{business_phone_number_id}/messages"
#     headers = {"Authorization": f"Bearer {GRAPH_API_TOKEN}"}
#     data = {
#         "messaging_product": "whatsapp",
#         "to": message['from'],
#         "text": {"body": "Echo: " + message['text']['body']},
#         "context": {
#             "message_id": message['id'],
#         },
#     }
#     response = requests.post(url, headers=headers, json=data)
#     if response.status_code != 200:
#         print(f"Error sending message: {response.content}")