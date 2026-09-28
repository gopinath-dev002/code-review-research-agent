from langchain_groq import ChatGroq
from ..setting import credentials

class Config:

    def get_llm(self,max_tokens,temperature):
        return ChatGroq(
            model=credentials.groq_model,
            api_key=credentials.groq_api_key,
            temperature=temperature,
            max_tokens=max_tokens
        )

config=Config()