#Create a hello world API using FastAPI.
#Run the server using uvicorn.
#Use the API documentation to learn how to use it.
#Submit the URL of your API and a screenshot of the documentation.
#Example: https://hello-world-fastapi.herokuapp.com/docs

from fastapi import FastAPI
import uvicorn
from pydantic import BaseModel
from langchain.chat_models import AzureChatOpenAI
from common.utils import BingSearchTool, run_agent
from langchain.memory import CosmosDBChatMessageHistory, ConversationBufferWindowMemory
import os
from langchain.agents import ConversationalChatAgent, AgentExecutor
from common.prompts import CUSTOM_CHATBOT_PREFIX, CUSTOM_CHATBOT_SUFFIX

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/message/{user_id}/{session_id}")
async def hello_name(user_id: str, session_id: str, question: str):
    llm = AzureChatOpenAI(deployment_name="gpt-4-32k", temperature=0.5, max_tokens=1000)
    www_search = BingSearchTool(llm=llm, k=5, return_direct=True)
    
    tools = [www_search]

    # Set brain Agent with persisten memory in CosmosDB
    cosmos = CosmosDBChatMessageHistory(
                    cosmos_endpoint=os.environ['AZURE_COSMOSDB_ENDPOINT'],
                    cosmos_database=os.environ['AZURE_COSMOSDB_NAME'],
                    cosmos_container=os.environ['AZURE_COSMOSDB_CONTAINER_NAME'],
                    connection_string=os.environ['AZURE_COMOSDB_CONNECTION_STRING'],
                    session_id=session_id,
                    user_id=user_id
                )
    cosmos.prepare_cosmos()
    memory = ConversationBufferWindowMemory(memory_key="chat_history", return_messages=True, k=30, chat_memory=cosmos)
    agent = ConversationalChatAgent.from_llm_and_tools(llm=llm, tools=tools,system_message=CUSTOM_CHATBOT_PREFIX,human_message=CUSTOM_CHATBOT_SUFFIX)
    agent_chain = AgentExecutor.from_agent_and_tools(agent=agent, tools=tools, memory=memory)

    answer = run_agent(question, agent_chain)
    return {"answer": answer, "session_id": session_id, "user_id": user_id}

#create main function to start fast api
if __name__ == "__main__":
    uvicorn.run(app)
