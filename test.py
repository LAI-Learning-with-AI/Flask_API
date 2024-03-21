import requests


def chat_tests():
    print("\n\n=========Testing Chat Endpoint...=========")
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
    print("\n\n=========Chat Endpoint Tests Complete=========")


def quiz_tests():
    print("\n\n=========Testing Quiz Endpoint...=========")

    quiz_data = {
        "userId": "123",
        "numberOfQuestions": 20,
        "types": ["TRUE_FALSE", "MULTIPLE_CHOICE", "SHORT_ANSWER", "CODING"],
        "topics": ["topic1", "topic2", "topic3"]
    }
    print("\n\n=========Testing Generate Quiz Endpoint...=========")
    generate_response = requests.post("http://127.0.0.1:5000/generatequiz", json=quiz_data)
    print(f"Generate Status Code: {generate_response.status_code}\nGenerate Response: {generate_response.json()}")
    print("\n\n=========Quiz Endpoint Tests Complete=========")


def get_similar_tests():
    print("\n\n=========Testing Get Similar Endpoint...=========")
    get_similar_data = {
        "topics": ["Computer Vision", "Backpropagation", "Deep Learning"],
        "max_resources_per_topic": 5
    }

    get_similar_response = requests.post("http://127.0.0.1:5000/getsimilar", json=get_similar_data)
    print(
        f"Get Similar Status Code: {get_similar_response.status_code}\nGet Similar Response: {get_similar_response.json()}")
    print("\n\n=========Get Similar Endpoint Tests Complete=========")


def run_tests():
    print("\n\n=========Running Tests...=========")
    # chat_tests() # Out of date
    # quiz_tests() # Out of date
    get_similar_tests()
    print("\n\n=========Done!=========")


if __name__ == "__main__":
    run_tests()
