from typing import Dict, List, Optional, Union

from pydantic import BaseModel

class RagContractReviewRequest(BaseModel):
    user_prompt: str
    file: str

class RagContractReviewResponse(BaseModel):
    type: str
    delta: Optional[Union[str, Dict[str, str], List[Dict[str, str]]]] = None
