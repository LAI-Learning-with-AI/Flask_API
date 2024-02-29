import requests

chat_data = {
    "userId": "123",
    "chatId": "456",
    "message": "What is deep learning?",
    "context": {
        "previous": [],
        "userData": {}
    }
}

chat_response = requests.post("http://127.0.0.1:5000/chat", json=chat_data)
print(f"Chat Status Code: {chat_response.status_code}\nChat Response: {chat_response.json()}")
