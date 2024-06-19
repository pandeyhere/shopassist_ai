import ast
import re

def extract_dictionary_from_string(string):
    try:
        regex_pattern = r"\{[^{}]+\}"

        dictionary_matches = re.findall(regex_pattern, string)

        # Extract the first dictionary match and convert it to lowercase
        if dictionary_matches:
            dictionary_string = dictionary_matches[0]
            dictionary_string = dictionary_string.lower()

            # Convert the dictionary string to a dictionary object using ast.literal_eval()
            dictionary = ast.literal_eval(dictionary_string)
    except Exception as e:
        print(e)
        raise Exception(f"Extraction from dictionary failed.")
    return dictionary