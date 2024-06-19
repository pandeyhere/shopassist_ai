function_descriptions = [
    {
        "name": "compare_laptops_with_user",
        "description": "Get the top 3 laptops from the catalogue, that best matches what the user is asking based on 'GPU intensity', 'Display Quality', 'Portability, 'Multitasking', 'Processing speed', 'Budget' '",
        "parameters": {
            "type": "object",
            "properties": {
                "gpu intensity" : {
                    "type" : "string",
                    "description" : "The requirement of the user in GPU capacity classified as low, medium or high",
                },
                "display quality" : {
                    "type": "string",
                    "description" : "The requirement of the user for Laptop's Display Quality & capacity classified as low, medium or high",
                },
                "portability" : {
                    "type" : "string",
                    "description" : "The requirement of the user for Laptop's portability classified as low, medium or high",
                },
                "multitasking": {
                    "type" : "string",
                    "description" : "The requirement of the user for Laptop's multitasking classified as low, medium or high",
                },
                "processing speed":{
                    "type" : " string",
                    "description" : "The requirement of the user for Laptop's Processing speed classified as low, medium or high",
                },
                "budget" : {
                    "type" : "integer",
                    "description" : "The maximum budget of the user"
                },
            },
            "required": ["GPU intensity", "Display quality", "Portability", "Multitasking", "Processing speed", "Budget"],
        },
    }
]