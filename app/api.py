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
        elif text == 'invoice':
            send_message(business_phone_number_id, message, "Please send the invoice image. Format: JPG, PNG, PDF")
        else:
            send_message(business_phone_number_id, message, "I didn't understand that. Please try again or send 'stop' to end the conversation or Message 'Hi' to start again.")

    elif message.get('type') == 'image':
        handle_image_message(business_phone_number_id, message)
        

    return {"status": "success"}

def has_greeted(message):
    # Implement logic to check if the user has greeted the bot before
    # This could involve checking a database or keeping track of the conversation state
    return True  # For now, we assume the user hasn't greeted the bot

def handle_image_message(business_phone_number_id, message):
    # Implement image handling logic here
    pass
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