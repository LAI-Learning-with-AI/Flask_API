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

quiz_data = {
    "userId": "123",
    "numberOfQuestions": 20,
    "types": ["TRUE_FALSE", "MULTIPLE_CHOICE", "SHORT_ANSWER", "CODING"],
    "topics": ["topic1", "topic2", "topic3"]
}

print("\n\n=========Testing Chat Endpoint...=========")
chat_response = requests.post("http://127.0.0.1:5000/chat", json=chat_data)
print(f"Chat Status Code: {chat_response.status_code}\nChat Response: {chat_response.json()}")

print("\n\n=========Testing Generate Quiz Endpoint...=========")
generate_response = requests.post("http://127.0.0.1:5000/generatequiz", json=quiz_data)
print(f"Generate Status Code: {generate_response.status_code}\nGenerate Response: {generate_response.json()}")

print("\n\n=========Done!=========")
