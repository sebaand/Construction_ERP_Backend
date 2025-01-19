from typing import Dict, List, Optional, Union, Literal
from pydantic import BaseModel, Field
import json
from pathlib import Path
from typing import List, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define valid element types
ElementType = Literal["table", "text", "date", "signature", "integer", "float", "checkbox"]


class HeaderTitle(BaseModel):
    name: str

class HeaderSubtitles(BaseModel):
    name: Optional[str] = None

class Header(BaseModel):
    mainTitle: HeaderTitle
    subTitles: HeaderSubtitles

class Column(BaseModel):
    name: str
    elementType: ElementType

class FormField(BaseModel):
    form_index: int
    name: Optional[str] = None
    elementType: ElementType
    columns_count: Optional[int] = Field(None, description="Required only if elementType is 'table'")
    rows_count: Optional[int] = Field(None, description="Required only if elementType is 'table'")
    columns: Optional[List[Column]] = Field(None, description="Required only if elementType is 'table'")

    def validate_table_fields(self) -> bool:
        """Validate that table-specific fields are present when elementType is 'table'"""
        if self.elementType == "table":
            return all([
                self.columns_count is not None,
                self.rows_count is not None,
                self.columns is not None
            ])
        return True

class FormStructure(BaseModel):
    header: Header
    formFields: List[FormField]

    def validate_form_indices(self) -> bool:
        """Validate that form indices are sequential starting from 1"""
        indices = [field.form_index for field in self.formFields]
        return indices == list(range(1, len(indices) + 1))

# Example usage and validation
def validate_form_schema(schema_dict: Dict) -> bool:
    try:
        # Extract the inner formStructure content
        form_structure = schema_dict.get("formStructure")
        if not form_structure:
            raise ValueError("Missing formStructure key")
            
        # Parse the schema into our model
        form = FormStructure.model_validate(form_structure)  # Changed this line
        
        # Additional validations
        if not form.validate_form_indices():
            raise ValueError("Form indices must be sequential starting from 1")
        
        for field in form.formFields:
            if not field.validate_table_fields():
                raise ValueError(f"Missing required table fields for form index {field.form_index}")
        
        return True
    except Exception as e:
        print(f"Validation failed: {str(e)}")
        return False


def load_and_validate_json_files(log_directory: str = "logs") -> Dict[str, bool]:
    log_dir = Path(log_directory)
    validation_results = {}
    
    for json_file in log_dir.glob("*.json"):
        try:
            # Load JSON file
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Get the content string and parse it into a JSON object
            content_str = data.get('content', '')
            try:
                content_obj = json.loads(content_str)  # Parse the stringified JSON
                # Now validate the actual form structure
                is_valid = validate_form_schema(content_obj)
                
                if not is_valid:
                    # Add detailed error logging
                    try:
                        FormStructure.model_validate(content_obj)
                    except Exception as validation_error:
                        logger.error(f"Detailed validation errors for {json_file.name}:")
                        for error in validation_error.errors():
                            logger.error(f"Field: {error['loc']}")
                            logger.error(f"Error: {error['msg']}")
                            logger.error(f"Error Type: {error['type']}\n")
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse content JSON string in {json_file}: {str(e)}")
                validation_results[json_file.name] = False
                continue
                
            validation_results[json_file.name] = is_valid
            
        except Exception as e:
            logger.error(f"Error processing file {json_file}: {str(e)}")
            validation_results[json_file.name] = False
    
    return validation_results

def summarize_validation_results(results: Dict[str, bool]) -> None:
    """
    Print a summary of validation results.
    
    Args:
        results (Dict[str, bool]): Dictionary of filename to validation result
    """
    total_files = len(results)
    valid_files = sum(1 for result in results.values() if result)
    
    print("\nValidation Summary:")
    print(f"Total files processed: {total_files}")
    print(f"Valid schemas: {valid_files}")
    print(f"Invalid schemas: {total_files - valid_files}")
    print(f"Success rate: {(valid_files/total_files)*100 if total_files > 0 else 0:.2f}%")
    
    if total_files - valid_files > 0:
        print("\nInvalid files:")
        for filename, is_valid in results.items():
            if not is_valid:
                print(f"- {filename}")

def debug_schema(json_file_path: str) -> None:
    """
    Debug a specific JSON file against the schema.
    """
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Parse the content string
        content_str = data.get('content', '')
        content_obj = json.loads(content_str)
        
        # Try to validate and catch specific issues
        try:
            FormStructure.model_validate(content_obj)
            print("Schema is valid!")
        except Exception as e:
            print("Schema validation failed. Details:")
            for error in e.errors():
                print(f"\nLocation: {' -> '.join(str(x) for x in error['loc'])}")
                print(f"Error: {error['msg']}")
                print(f"Error Type: {error['type']}")
                
            # Print the actual structure we're trying to validate
            print("\nActual structure being validated:")
            print(json.dumps(content_obj, indent=2))
            
    except Exception as e:
        print(f"Error processing file: {str(e)}")


if __name__ == "__main__":
    # Debug a specific file
    debug_schema("logs/form_analysis_20250116_105512.json")
    
    # Or validate all files
    validation_results = load_and_validate_json_files()
    summarize_validation_results(validation_results)