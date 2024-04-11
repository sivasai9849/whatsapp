from fastapi import FastAPI, Request, HTTPException, Response
import os
import requests
from pydantic import BaseModel
from typing import List, Optional
import json


app = FastAPI()

WEBHOOK_VERIFY_TOKEN = os.getenv("WEBHOOK_VERIFY_TOKEN")
GRAPH_API_TOKEN = os.getenv("GRAPH_API_TOKEN")

class Button(BaseModel):
    type: str
    title: str
    reply: str

class Message(BaseModel):
    messaging_product: str
    to: str
    type: Optional[str] = None
    text: Optional[str] = None
    buttons: Optional[List[Button]] = []
    
class InvoiceProcessingState:
    def __init__(self):
        self.state = "greeting"
        self.invoice_file = None
        self.phone_number = None
        
    def reset(self):
        self.state = "greeting"
        self.invoice_file = None
        self.phone_number = None
        
state = InvoiceProcessingState()

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()

    # message = data.get('entry', [{}])[0].get('changes', [{}])[0].get('value', {}).get('messages', [{}])[0]

    # if message.get('type') == 'text':
    #     business_phone_number_id = data.get('entry', [{}])[0].get('changes', [{}])[0].get('value', {}).get('metadata', {}).get('phone_number_id')

    #     send_message(business_phone_number_id, message)
    
    entry = data.get('entry', [])
    business_phone_number_id = data.get('entry', [{}])[0].get('changes', [{}])[0].get('value', {}).get('metadata', {}).get('phone_number_id')
    
    for event in entry:
        incoming_message = event["changes"][0]['value']['messages'][0]
        state.phone_number = incoming_message['from']
        if state.state == "greeting":
            user_message = incoming_message['text']['body'].lower()
            if user_message == 'hi' or user_message == 'hello':
                buttons = [
                    Button(type="reply", title="process_invoice", reply="Process Invoice"),
                    Button(type="reply", title="process_receipt", reply="Process Receipt"),
                ]
                response = Message(messaging_product="whatsapp", to=state.phone_number, text="Hello! What do you need to process?", buttons=buttons)
                state.state = "process_selection"
            else:
                response = Message(messaging_product="whatsapp", to=state.phone_number, text="Hi! I am an invoice processing bot. Please type 'hi' or 'hello' to start.")
        elif state.state == "process_selection":
            user_message = incoming_message.get("button_reply", {}).get("title", "").lower()
            if user_message == "process invoice":
                response = Message(messaging_product="whatsapp", to=state.phone_number, text="Please upload the invoice in JPEG or PDF format.")
                state.state = "invoice_upload"
            elif user_message == "process receipt":
                response = Message(messaging_product="whatsapp", to=state.phone_number, text="Receipt processing is not implemented yet.")
            else:
                response = Message(messaging_product="whatsapp", to=state.phone_number, text="Invalid option. Please select 'Process Invoice' or 'Process Receipt'.")
        elif state.state == "invoice_upload":
            if incoming_message.get("type") == "document":
                state.invoice_file = incoming_message["document"]
                response = Message(messaging_product="whatsapp", to=state.phone_number, text="Invoice processing started. You will receive the results soon.")
                state.reset()
            else:
                response = Message(messaging_product="whatsapp", to=state.phone_number, text="No file was uploaded. Please try again.")
        else:
            response = Message(messaging_product="whatsapp", to=state.phone_number, text="Something went wrong. Please start over.")
            state.reset()

        await send_response(response, business_phone_number_id)

    return {"message": "Webhook received"}

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
        
import requests

def send_response(response: Message, business_phone_number_id: str):
    url = f"https://graph.facebook.com/v18.0/{business_phone_number_id}/messages"
    headers = {"Authorization": f"Bearer {GRAPH_API_TOKEN}"}

    data = {
        "messaging_product": response.messaging_product,
        "to": response.to,
        "type": "interactive" if response.buttons else "text",
    }

    if response.text:
        data["text"] = {"body": response.text}

    if response.buttons:
        data["interactive"] = {
            "type": "button",
            "body": {"text": response.text},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": button.reply, "title": button.title}}
                    for button in response.buttons
                ]
            },
        }

    response = requests.post(url, headers=headers, json=data)
    if response.status_code != 200:
        print(f"Error sending message: {response.content}")