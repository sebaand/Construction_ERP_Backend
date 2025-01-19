from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Callable, Tuple
from app.utils.llm_call import llm_call

# Define processing steps with their system prompts
ProcessingStep = Tuple[str, str]  # (prompt, system_prompt)

def chain(input: str, steps: List[ProcessingStep], pdf_path: str) -> str:
    """Chain multiple LLM calls sequentially, passing results between steps."""
    result = input
    for i, (prompt, system_prompt) in enumerate(steps, 1):
        print(f"\nStep {i}:")
        result = llm_call(f"{prompt}\nInput: {result}", pdf_path, system_prompt)
        print(result)
    return result

def parallel(steps: List[ProcessingStep], pdf_path: str, n_workers: int = 3) -> List[str]:
    """Process multiple inputs concurrently with their respective system prompts."""
    with ThreadPoolExecutor(max_workers=n_workers) as executor:
        futures = [
            executor.submit(
                llm_call, 
                prompt,
                pdf_path,
                system_prompt
            ) for prompt, system_prompt in steps
        ]
        return [f.result() for f in futures]
    

data_processing_test1: List[ProcessingStep] = [
    (
    """You are helping me analyze the core components of a form. A form can have the following elements: tables or single entry fields like date_input, signature, text_input, number_input. Extract the headers of each form element. If a header is not present mark it as empty. For tables, don't extract the column headers, only extract a table header if it exists. Don’t provide any further explanation!
    Example format:
    Form_Titles = [Title : “Training & Development Plan”, Subtitle : “Toolbox Talk 2024”]
    Form_Element_Headers = [0 : “Toolbox Talk Overview”, 1 : “Candidates Details”, 2 : “Date of Attendance”, 3 : “Signature”]""",
    "Your output should strictly follow the output template: Form_Element_Headers = [0 : “Header Sample, 1 : “Header Sample”, 2 : “Header Sample”, 3 : ”Header Sample”]"
    ),
]


data_processing_test: List[ProcessingStep] = [
    # (
    # """Analyze the form's header section and output a JSON structure that includes:
    # 1. The main title of the form
    # 2. Any subtitle text, maintaining line breaks with \n
    # Don’t provide any further explanation!
    # Format the output as:
    # {
    # 'header': {
    #     'mainTitle': {'name': 'exact_title_text'},
    #     'subTitles': {'name': 'exact_subtitles_with_linebreaks'}
    # }
    # }
    # Don’t provide any further explanation!""",
    # """Your output should strictly follow the output template: 
    # {
    # 'header': {
    #     'mainTitle': {'name': 'exact_title_text'},
    #     'subTitles': {'name': 'exact_subtitles_with_linebreaks'}
    # }
    # }"""
    # ),
    # (
    # """Identify all distinct form sections. For each section output:
    # 1. A sequential form_index starting at 1
    # 2. A descriptive name for the section
    # 3. The element type. Potential elementTypes are: “table”,”text”,”date”,"signature","integer","float",
    # Don’t provide any further explanation!
    # Output format:
    # {
    # 'sections': [
    #     {
    #     'form_index': number,
    #     'name': 'section_name',
    #     'elementType': 'element_type'
    #     }
    # ]
    # }
    # Don’t provide any further explanation!""",
    # """Your additional output should strictly follow the output template: 
    # {
    # 'sections': [
    #     {
    #     'form_index': number,
    #     'name': 'section_name',
    #     'elementType': 'element_type'
    #     }
    # ]
    # }"""
    # ),
    (
    """For each table section identified, analyze and output:
    1. Column count
    2. Row count
    3. Column definitions including name and element type

    Sample Output:
    {
    "formStructure": {
        "header": {
        "mainTitle": {
            "name": "TOOLBOX TALK 2024"
        },
        "subTitles": {
            "name": "TRAINING AND DEVELOPMENT PLAN\nTRAINING SESSION ATTENDANCE SHEET"
        }
        },
        "formFields": [
        {
            "form_index": 1,
            "name": "Session Details",
            "elementType": "table",
            "columns_count": 2,
            "rows_count": 4,
            "columns": [
            {
                "name": "Title",
                "elementType": "text"
            },
            {
                "name": "Date",
                "elementType": "date"
            },
            {
                "name": "Location",
                "elementType": "text"
            },
            {
                "name": "Start Time",
                "elementType": "text"
            },
            {
                "name": "Duration",
                "elementType": "integer"
            },
            {
                "name": "End Time",
                "elementType": "text"
            },
            {
                "name": "Presenters Name",
                "elementType": "text"
            },
            {
                "name": "Presenters Signature",
                "elementType": "signature"
            }
            ]
        },
        {
            "form_index": 2,
            "name": "Attendance Record",
            "elementType": "table",
            "columns_count": 3,
            "rows_count": 6,
            "columns": [
            {
                "name": "Candidate's Name",
                "elementType": "text"
            },
            {
                "name": "Name of Candidate's Employer",
                "elementType": "text"
            },
            {
                "name": "Candidate's Signature",
                "elementType": "signature"
            }
            ]
        },
        {
            "form_index": 3,
            "name": "Grant Claim Information",
            "elementType": "table",
            "columns_count": 4,
            "rows_count": 1,
            "columns": [
            {
                "name": "No. Attended",
                "elementType": "integer"
            },
            {
                "name": "Duration",
                "elementType": "float"
            },
            {
                "name": "Total Time",
                "elementType": "float"
            },
            {
                "name": "Employer Reference",
                "elementType": "text"
            }
            ]
        }
        ]
    }
    }
    Don’t provide any further explanation!""",
    """Your additional output should strictly follow the styling provided by the sample"""
    ),
    # (
    # """Combine the previous outputs into a single schema following this structure:
    # {
    # 'formStructure': {
    #     'header': [Header Analysis Output],
    #     'formFields': [Combine Sections with Table Structures]
    # }
    # }
    # Don’t provide any further explanation!""",      
    # """Your output should strictly follow the output template:
    # {
    #     'formStructure': {
    #         'header': [Header Analysis Output],
    #         'formFields': [Combine Sections with Table Structures]
    #     }
    # }"""
    # )
]

starting_input = ""

formatted_result = chain(starting_input, data_processing_test,'pdfs/LIFTING OPERATIONS AND LIFTING EQUIPMENT - REPORT OF INSPECTION (SECTION A).pdf')
# print(formatted_result)


# impact_results = parallel(
#     data_processing_test,'pdfs/Toolbox Talk.pdf'
# )

# for result in impact_results:
#     print(result)

