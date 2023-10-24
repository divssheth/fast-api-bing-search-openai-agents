from typing import Dict, Union
import base64
import html
from langchain.chat_models import AzureChatOpenAI

from langchain.schema import OutputParserException
from langchain.chains import LLMChain
from langchain.tools import BaseTool
from langchain.prompts import PromptTemplate

from langchain.agents import AgentExecutor, initialize_agent, AgentType
from langchain.tools import BaseTool
from langchain.utilities import BingSearchAPIWrapper

try:
    from .prompts import (BING_PROMPT_PREFIX)
except Exception as e:
    print(e)
    from prompts import (BING_PROMPT_PREFIX)


def text_to_base64(text):
    # Convert text to bytes using UTF-8 encoding
    bytes_data = text.encode('utf-8')

    # Perform Base64 encoding
    base64_encoded = base64.b64encode(bytes_data)

    # Convert the result back to a UTF-8 string representation
    base64_text = base64_encoded.decode('utf-8')

    return base64_text


def table_to_html(table):
    table_html = "<table>"
    rows = [sorted([cell for cell in table.cells if cell.row_index == i], key=lambda cell: cell.column_index) for i in range(table.row_count)]
    for row_cells in rows:
        table_html += "<tr>"
        for cell in row_cells:
            tag = "th" if (cell.kind == "columnHeader" or cell.kind == "rowHeader") else "td"
            cell_spans = ""
            if cell.column_span > 1: cell_spans += f" colSpan={cell.column_span}"
            if cell.row_span > 1: cell_spans += f" rowSpan={cell.row_span}"
            table_html += f"<{tag}{cell_spans}>{html.escape(cell.content)}</{tag}>"
        table_html +="</tr>"
    table_html += "</table>"
    return table_html


# Returning the toekn limit based on model selection
def model_tokens_limit(model: str) -> int:
    """Returns the number of tokens limits in a text model."""
    if model == "gpt-35-turbo":
        token_limit = 4096
    elif model == "gpt-4":
        token_limit = 8192
    elif model == "gpt-35-turbo-16k":
        token_limit = 16384
    elif model == "gpt-4-32k":
        token_limit = 32768
    else:
        token_limit = 4096
    return token_limit

def run_agent(question:str, agent_chain: AgentExecutor) -> str:
    """Function to run the brain agent and deal with potential parsing errors"""
    
    for i in range(5):
        try:
            response = agent_chain.run(input=question)
            break
        except OutputParserException as e:
            # If the agent has a parsing error, we use OpenAI model again to reformat the error and give a good answer
            chatgpt_chain = LLMChain(
                    llm=agent_chain.agent.llm_chain.llm, 
                        prompt=PromptTemplate(input_variables=["error"],template='Remove any json formating from the below text, also remove any portion that says someting similar this "Could not parse LLM output: ". Reformat your response in beautiful Markdown. Just give me the reformated text, nothing else.\n Text: {error}'), 
                    verbose=False
                )

            response = chatgpt_chain.run(str(e))
            continue
    
    return response
    

######## TOOL CLASSES #####################################
###########################################################
    
class BingSearchResults(BaseTool):
    """Tool for a Bing Search Wrapper"""

    name = "@bing"
    description = "useful when the questions includes the term: @bing.\n"

    k: int = 5

    def _run(self, query: str) -> str:
        bing = BingSearchAPIWrapper(k=self.k)
        try:
            return bing.results(query,num_results=self.k)
        except:
            return "No Results Found"
    
    async def _arun(self, query: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("BingSearchResults does not support async")
            

class BingSearchTool(BaseTool):
    """Tool for a Bing Search Wrapper"""
    
    name = "@bing"
    description = "useful when the questions includes the term: @bing.\n"
    
    llm: AzureChatOpenAI
    k: int = 5
    
    def _run(self, tool_input: Union[str, Dict],) -> str:
        try:
            tools = [BingSearchResults(k=self.k)]
            parsed_input = self._parse_input(tool_input)

            agent_executor = initialize_agent(tools=tools, 
                                              llm=self.llm, 
                                              agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, 
                                              agent_kwargs={'prefix':BING_PROMPT_PREFIX},
                                              callback_manager=self.callbacks,
                                              verbose=self.verbose)
            
            for i in range(2):
                try:
                    response = run_agent(parsed_input, agent_executor)
                    break
                except Exception as e:
                    response = str(e)
                    continue

            return response
        
        except Exception as e:
            print(e)
    
    async def _arun(self, query: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("BingSearchTool does not support async")