import openai
import pandas as pd
from util import util
import json, os, ast
from modules.custom_function import function_descriptions
from modules.score_comparison import compare_laptops_with_user
from tenacity import retry, wait_random_exponential, stop_after_attempt

openai.api_key= os.getenv("OPENAI_API_KEY")




def initialize_conversation():
    '''
    Returns a list [{"role": "system", "content": system_message}]
    '''

    delimiter = "####"

    example_user_dict = {'GPU intensity': "high",
                        'Display quality':"high",
                        'Portability': "low",
                        'Multitasking': "high",
                        'Processing speed': "high",
                        'Budget': "150000"}

    example_user_req = {'GPU intensity': "_",
                        'Display quality': "_",
                        'Portability': "_",
                        'Multitasking': "_",
                        'Processing speed': "_",
                        'Budget': "_"}

    system_message = f"""
    You are an intelligent laptop gadget expert and your goal is to find the best laptop for a user.
    You are trying to understand the user's requirement for these laptop's features: {'gpu intensity', 'display quality', 'portability', 'multitasking', 'processing speed', 'budget'}.
    You need to ask relevant questions and understand the user need for each feature by analysing the user's responses.
    After understanding their requirements, you'll use a function call to suggest the top 3 laptops with their respective user match score.
    Recommend these laptops and answer any user;s query about them.

    {delimiter} Here are certain guidelines that you need to follow:
    Don't ask questions about more than 2 features at a time.
    If the user's budget is less than 25000 INR, please mention that there are no laptops in that range.
    Recommend the top3 laptops in the following format:
    Start with a brief summary of each laptop in the following format, in decreasing order of price of laptops:
    1. <Laptop Name> : <Major Specifications of the laptop>, <Price in Rs>
    2. <Laptop Name> : <Major Specifications of the laptop>, <Price in Rs>
    3. <Laptop Name> : <Major Specifications of the laptop>, <Price in Rs>
    {delimiter}

    {delimiter} To find the top3 laptops, you need to have the following chain of thoughts:
    Thought 1: Ask one question to understand the user's profile and requirements. \n
    If their primary use for the laptop is unclear. Ask another question to comprehend their needs.
    Answer "Yes" or "No" to indicate if you understand the requirements. \n
    If yes, proceed to the next step. Otherwise, rephrase the question to capture their profile. \n

    Though 2: Now, you are trying to understand the requirements for other features which you couldn't in the previous step.
    Ask questions to strengthen your understanding of the user's profile.
    Don't ask questions about more than 2 features at a time.
    Answer "Yes" or "No" to indicate if you understood all the needs of the features and are confident about the same.
    If yes, move to the next Thought. If no, ask question on the features whose needs you are unsure of. \n
    It is a good practice to ask question with a sound logic as opposed to directly citing the feature you want to understand the need for. {delimiter}
    {delimiter}

    {delimiter} Here is a sample conversation between the user and assistant:
    Assistant: "Hello! I'm here to help you find the perfect laptop that suits your needs. Could you please share your requirements?"
    User: "Hi, I am an editor."
    Assistant: "Great! As an editor, you likely require a laptop that can handle demanding tasks. Hence, the laptop should have high multitasking capability. You would also need a high end display for better visuals and editing. May I know what kind of work do you primarily focus on? Are you more involved in video editing, photo editing, or both? Understanding the specific type of editing work will help me tailor my recommendations accordingly. Let me know if my understanding is correct until now."
    User: "I primarily work with After Effects."
    Assistant: "Thank you for providing that information. Working with After Effects involves working with graphics, animations, and rendering, which will require high GPU. Do you work with high-resolution media files, such as 4K videos or RAW photos? Understanding your file sizes will help determine the storage capacity and processing power needed."
    User: "Yes, sometimes I work with 4K videos as well."
    Assistant: "Thank you for the information. Processing 4K vidoes will require a good processor and high GPU. I think we have already determined earlier that you need a high GPU. To ensure I have a complete understanding of your needs, I have one more question: Are you frequently on the go and require a laptop that is lightweight and easy to carry, or do you primarily work from a stationary location?"
    User: "Yes, sometimes I travel but do not carry my laptop."
    Assistant:"Could you kindly let me know your budget for the laptop? This will help me find options that fit within your price range while meeting the specified requirements."
    User: "my max budget is 1.5lakh inr"
    {delimiter}

    Start with a short welcome message and encourage the user to share their requirements.
    """
    conversation = [{"role": "system", "content": system_message}]
    # conversation = system_message
    return conversation

# Define a Chat Completions API call
# Retry up to 6 times with exponential backoff, starting at 1 second and maxing out at 20 seconds delay
@retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(6))
def get_chat_model_completions(messages):
    MODEL = 'gpt-4-0613'

    try:
        response = openai.chat.completions.create(
            model = MODEL,
            messages = messages,
            temperature = 0,
            max_tokens = 500,
            functions = function_descriptions,
            function_call="auto",
            )
    except Exception as e:
        print(e)
        raise Exception(f"Could not communicate to Open AI Server.")


    return response.choices[0].message


def moderation_check(user_input):
    try:
        response = openai.Moderation.create(input=user_input)
        moderation_output = response["results"][0]
        if moderation_output["flagged"] == True:
            return "Flagged"
        else:
            return "Not Flagged"
    except Exception as e:
        print(e)
        raise Exception(f"Moderation could not be checked.")
def intent_confirmation_layer(response_assistant):
    try:
        delimiter = "####"
        prompt = f"""
        You are a senior evaluator who has an eye for detail.
        You are provided an input. You need to evaluate if the input has the following keys: 'GPU intensity','Display quality','Portability','Multitasking',' Processing speed','Budget'
        Next you need to evaluate if the keys have the the values filled correctly.
        The values for all keys, except 'budget', should be 'low', 'medium', or 'high' based on the importance as stated by user. The value for the key 'budget' needs to contain a number with currency.
        Output a string 'Yes' if the input contains the dictionary with the values correctly filled for all keys.
        Otherwise out the string 'No'.

        Here is the input: {response_assistant}
        Only output a one-word string - Yes/No.
        """


        confirmation = openai.Completion.create(
                                        model="text-davinci-003",
                                        prompt = prompt,
                                        temperature=0)
    except Exception as e:
        print(e)
        raise Exception(f"Intent could not be confirmed.")


    return confirmation["choices"][0]["text"]

def dictionary_present(response):
    delimiter = "####"
    user_req = {'GPU intensity': 'high','Display quality': 'high','Portability': 'medium','Multitasking': 'high','Processing speed': 'high','Budget': '200000 INR'}
    prompt = f"""You are a python expert. You are provided an input.
            You have to check if there is a python dictionary present in the string.
            It will have the following format {user_req}.
            Your task is to just extract and return only the python dictionary from the input.
            The output should match the format as {user_req}.
            The output should contain the exact keys and values as present in the input.

            Here are some sample input output pairs for better understanding:
            {delimiter}
            input: - GPU intensity: low - Display quality: high - Portability: low - Multitasking: high - Processing speed: medium - Budget: 50,000 INR
            output: {{'GPU intensity': 'low', 'Display quality': 'high', 'Portability': 'low', 'Multitasking': 'high', 'Processing speed': 'medium', 'Budget': '50000'}}

            input: {{'GPU intensity':     'low', 'Display quality':     'high', 'Portability':    'low', 'Multitasking': 'high', 'Processing speed': 'medium', 'Budget': '90,000'}}
            output: {{'GPU intensity': 'low', 'Display quality': 'high', 'Portability': 'low', 'Multitasking': 'high', 'Processing speed': 'medium', 'Budget': '90000'}}

            input: Here is your user profile 'GPU intensity': 'high','Display quality': 'high','Portability': 'medium','Multitasking': 'low','Processing speed': 'high','Budget': '200000 INR'
            output: {{'GPU intensity': 'high','Display quality': 'high','Portability': 'medium','Multitasking': 'high','Processing speed': 'low','Budget': '200000'}}
            {delimiter}

            Here is the input {response}

            """
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt,
        max_tokens = 2000
        # temperature=0.3,
        # top_p=0.4
    )
    return response["choices"][0]["text"]

def dialogue_mgmt_system():
    try:
        conversation = initialize_conversation()
        introduction = get_chat_model_completions(conversation)
        print(introduction + '\n')
        top_3_laptops = None
        user_input = ""

        while(user_input != "exit"):
            user_input = input("")

            moderation = moderation_check(user_input)
            if moderation == 'Flagged':
                print("Sorry, this message has been flagged. Please restart your conversation.")
                break
            conversation.append({"role": "user", "content": user_input})

            response_assistant = get_chat_model_completions(conversation)

            if response_assistant.function_call:
                    
                moderation = moderation_check(response_assistant.function_call.arguments)
                if moderation == 'Flagged':
                    print("Sorry, this message has been flagged. Please restart your conversation.")
                    break

                confirmation = intent_confirmation_layer(response_assistant.function_call.arguments)

                moderation = moderation_check(confirmation)
                if moderation == 'Flagged':
                    print("Sorry, this message has been flagged. Please restart your conversation.")
                    break

                if "No" in confirmation:
                    conversation.append({"role": "assistant", "content": response_assistant.function_call.arguments})
                    print("\n" + response_assistant.function_call.arguments + "\n")
                    print('\n' + confirmation + '\n')
                else:
                    print("\n" + response_assistant.function_call.arguments + "\n")
                    print('\n' + confirmation + '\n')
                    response = dictionary_present(response_assistant.function_call.arguments)

                    moderation = moderation_check(response)
                    if moderation == 'Flagged':
                        print("Sorry, this message has been flagged. Please restart your conversation.")
                        break
                print('\n' + response + '\n')

                print("Thank you for providing all the information. Kindly wait, while I fetch the products: \n")

                function_name = response_assistant.function_call.name
                function_args = json.loads(response_assistant.function_call.arguments)
                top_3_laptops = compare_laptops_with_user(function_args)

                function_response = recommendation_validation(top_3_laptops)

                if len(function_response) == 0:
                    print("Sorry, we do not have laptops that match your requirements. Connecting you to a human expert.")
                    break

                conversation.append(response_assistant)
                conversation.append(
                    {
                        "role": "function",
                        "name": function_name,
                        "content": function_response,
                    }
                )

                recommendation = get_chat_model_completions(conversation)

                moderation = moderation_check(recommendation)
                if moderation == 'Flagged':
                    print("Sorry, this message has been flagged. Please restart your conversation.")
                    break


                conversation.append({"role": "assistant", "content": recommendation.content})

                print(recommendation.content + '\n')
            else:
                conversation.append({"role": "user", "content": response_assistant.content})
                print('\n' + response_assistant.content + '\n')
    except Exception as e:
        print(e)
        raise Exception(f"Error occurred during processing in chat bot.")

def recommendation_validation(laptop_recommendation):
    try:
        data = json.loads(laptop_recommendation)
        data1 = []
        for i in range(len(data)):
            if data[i]['Score'] > 2:
                data1.append(data[i])
    except Exception as e:
        print(e)
        raise Exception(f"Recommendation could not be validated.")

    return json.dumps(data1)



def initialize_conv_reco(products):
    system_message = f"""
    You are an intelligent laptop gadget expert and you are tasked with the objective to \
    solve the user queries about any product from the catalogue: {products}.\
    You should keep the user profile in mind while answering the questions.\

    Start with a brief summary of each laptop in the following format, in decreasing order of price of laptops:
    1. <Laptop Name> : <Major specifications of the laptop>, <Price in Rs>
    2. <Laptop Name> : <Major specifications of the laptop>, <Price in Rs>

    """
    conversation = [{"role": "system", "content": system_message }]
    return conversation

if __name__ == "__main__":
    dialogue_mgmt_system( )