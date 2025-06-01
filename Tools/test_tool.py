from langchain.agents import tool

def test_tool(input_text: str) -> str:
    """
    A simple test tool that returns the input text.
    
    Args:
        input_text (str): The input text to be returned.
        
    Returns:
        str: The same input text.
    """
    return input_text