# chatbot
A Chatbot to record a users headaches using Google Dialogflow to implement the chatbot, Twillio to be allow the user to message and communicate with the chatbot, Flask backend with Python to fascilitate communication between Twillio, Google Dialogflow and MySQL database hosted on PythonAnywhere server and the frontend using HTML, CSS and JavaScript.

The flow of data for the chatbot is as follows:
1) The user messaging the phone number for the chatbot from their phone. 
2) This information is forwarded from Twillio to the Flask backend.
3) The Flask backend checks if the user is signed in to the system.
4) The Flask backend checks with the MySQL DB server if the user is signed in, if the user is signed in it moves on to step 5. If the user is not registered in the system the Flask backend sends the user a message to signup page and if the user is registered but not signed in it sends them a link to the sign in page. 
5) The Flask backend cleans the data and sends the information to the Google Dialogflow API. 
6) The Google Dialogflow API processes the information and returns a response to the Flask backend while also storing the user input. 
7) The Flask backend sends this information to the user.
8) Steps 5-7 are repeated till the chatbot and user have completed their conversation.
9) Google Dialogflow on the end of the conversation contacts our Flask backend using a REST API call to store the information gathered.
10) The Flask backend then cleans the data sent by Google Dialogflow about the conversation with the user and then sends this information to the MySQL DB server to be stored.
11) The user can visit the webportal and view any of the headaches or medications they have reported in their conversations with the chatbot and also view in a visual graph various information about their headaches like number of headaches in the past few months, intensity of headaches, etc.
