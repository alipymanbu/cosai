from typing import List, Dict, Any

class State(Dict):
    messages: List[Any]
    analysis_report: str
    requested_method: str
    user_input: str
    tool_available: bool
    generated_code: str