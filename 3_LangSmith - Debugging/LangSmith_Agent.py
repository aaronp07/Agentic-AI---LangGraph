from typing import TypedDict, Annotated
from langgraph.graph.message import AnyMessage, add_messages
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool
import os
from dotenv import load_dotenv

load_dotenv()

os.environ['LANGSMITH_API_KEY'] = os.getenv('langsmith_api_key')

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    
llm = ChatOllama(model='mistral', temperature=0)

def make_default_graph():
    builder = StateGraph(State)
    
    def call_model(state):
        return {'messages': [llm.invoke(state['messages'])]}
    
    builder.add_node('agent', call_model)
    
    builder.add_edge(START, 'agent')
    builder.add_edge('agent', END)
    
    graph = builder.compile()
    return graph

def make_alternate_graph():
    
    @tool
    def add(a: float, b: float):
        """Adds two numbers."""
        return a+b
    
    tool_node = ToolNode([add])
    model_with_tools = llm.bind_tools(tools=[add])
    
    def call_model(state):
        return {'messages': [model_with_tools.invoke(state['messages'])]}
    
    def should_continue(state: State):
        last_msg = state['messages'][-1].content
        if 'tool' in last_msg:
            return 'tools'
        
        return END
    
    builder = StateGraph(State)
    
    builder.add_node('agent', call_model)
    builder.add_node('tools', tool_node)
    
    builder.add_edge(START, 'agent')
    builder.add_edge('tools', 'agent')
    builder.add_conditional_edges('agent', should_continue)
    
    agent = builder.compile()
    return agent

# agent_execute = make_default_graph()
agent_execute = make_alternate_graph()