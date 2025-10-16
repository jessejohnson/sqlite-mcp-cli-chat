from anthropic import Anthropic
from util import slog
from .messages import Message, UserMessage, AssistantMessage
from dataclasses import dataclass
from typing import Any
from google import genai
from google.genai import types
from openai import OpenAI
from settings import settings

class LLMClient:
    model_name: str = settings.MODEL_NAME
        
    def read_tool_result(self, tool_name, tool_input, tool_result) -> list[UserMessage]:
        user_messages = []
        for content in tool_result.content:
            user_messages.append(
                UserMessage(
                    content=f"Tool {tool_name} with inputs {tool_input} returned:\n{content.text}",
                    raw_content=content,
                    type=content.type
                )
            )
        return user_messages

@dataclass
class ModelResponse:
    messages: list[Message]
    tool_name: str | None = None 
    tool_input: dict[str, Any] | None = None
    should_use_tool: bool = False

class OpenAILLM(LLMClient):
    def __init__(self, url: str = None):
        if url is None:
            self.openai = OpenAI()
        else:
            self.openai = OpenAI(base_url=url)
    
    def send(self, message_history, tools) -> ModelResponse:
        import json

        input_messages = []
        for m in message_history:
            input_messages.append(
                {
                    "role": m.role,
                    "content": [{"type": "text", "text": m.content}]
                }
            )
        slog.debug(f"Parsed messages {input_messages}")
        tool_defs = []
        for t in tools:
            tool_defs.append(
                {
                    "type": "function",
                    "function": {
                        "name": t["name"],
                        "description": t["description"],
                        "parameters": t["input_schema"]
                    }
                }
            )
        slog.debug(f"tool_defs is {tool_defs}")
        response = self.openai.chat.completions.create(
            model=self.model_name,
            max_tokens=settings.MAX_TOKENS,
            messages=input_messages,
            tools=tool_defs
        )
        slog.debug(f"Model response is {response}")
        model_response = ModelResponse(
            messages=[]
        )
        completion = response.choices[0].message
        if completion.tool_calls is not None:
            tool_call = completion.tool_calls[0]
            model_response.should_use_tool = True
            model_response.tool_name = tool_call.function.name
            model_response.tool_input = json.loads(tool_call.function.arguments)
            model_response.messages.append(
                AssistantMessage(
                    content=f"""Using tool {model_response.tool_name} \
                    with inputs {model_response.tool_input}...""",
                    type="tool_use",
                    raw_content=completion
                )
            )
        elif completion.content is not None:
            model_response.messages.append(
                AssistantMessage(
                    content=completion.content,
                    type="text",
                    raw_content=completion
                )
            )
        return model_response

class GeminiLLM(LLMClient):
    def __init__(self):
        self.gemini = genai.Client()

    def send(self, message_history, tools) -> ModelResponse:
        input_messages = []
        for m in message_history:
            input_messages.append(
                f"{m.role}: {m.content}"
            )
        tool_defs = []
        for t in tools:
            tool_defs.append(
                {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": t["input_schema"]
                }
            )
        tools = types.Tool(function_declarations=tool_defs)

        config = types.GenerateContentConfig(tools=[tools])
        response = self.gemini.models.generate_content(
            model=self.model_name,
            contents="\n".join(input_messages),
            config=config
        )
        slog.debug(f"Gemini Response is {response}")
        model_response = ModelResponse(
            messages=[]
        )
        for part in response.candidates[0].content.parts:    
            slog.debug(f"Processing part {part}...")        
            if part.function_call:
                model_response.should_use_tool = True
                model_response.tool_name = part.function_call.name
                model_response.tool_input = part.function_call.args
                model_response.messages.append(
                    AssistantMessage(
                        content=f"""Using tool {model_response.tool_name}\
                         with inputs {model_response.tool_input}...""",
                        type="tool_use",
                        raw_content=part
                    )
                )
            elif hasattr(part, "text"):
                model_response.messages.append(
                    AssistantMessage(
                        content=part.text,
                        type="text",
                        raw_content=part
                    )
                )
        return model_response

class AnthropicLLM(LLMClient):
    def __init__(self):
        self.anthropic = Anthropic()

    def send(self, message_history, tools) -> ModelResponse:
        input_messages = []
        for m in message_history:
            input_messages.append(
                {
                    "role": m.role,
                    "content": [{"type": "text", "text": m.content}]
                }
            )
        slog.debug(f"Parsed messages {input_messages}")
        response = self.anthropic.messages.create(
            model=self.model_name,
            max_tokens=settings.MAX_TOKENS,
            messages=input_messages,
            tools=tools
        )
        model_response = ModelResponse(
            messages=[]
        )
        for content in response.content:
            if content.type == "tool_use":
                model_response.should_use_tool = True
                model_response.tool_name = content.name 
                model_response.tool_input = content.input
                model_response.messages.append(
                    AssistantMessage(
                        content=f"Using tool {model_response.tool_name} \
                        with inputs {model_response.tool_input}...",
                        type=content.type,
                        raw_content=content
                    )
                )
                slog.debug(f"tool_use response is {content}")
            elif content.type == "text": 
                model_response.messages.append(
                    AssistantMessage(
                        content=content.text,
                        type=content.type,
                        raw_content=content
                    )
                )
        return model_response

def get_llm_client() -> LLMClient:
    slog.info(f"{settings.MODEL_NAME} set up as LLM Client for {settings.LLM_SERVICE} service")
    if settings.LLM_SERVICE == "google":
        return GeminiLLM()
    elif settings.LLM_SERVICE == "anthropic":
        return AnthropicLLM()
    elif settings.LLM_SERVICE == "openai":
        if settings.OPENAI_BASE_URL is not None:
            return OpenAILLM(url=settings.OPENAI_BASE_URL)
        else:
            return OpenAILLM()