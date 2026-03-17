from typing import TypedDict,Dict,List,Annotated,Sequence
from dotenv import load_dotenv
from langgraph.graph import StateGraph,START,END
from langchain_core.messages import BaseMessage,ToolMessage,SystemMessage
from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

load_dotenv()

# Annotate - provides additional context without affecting the type itself

# Sequence- To automatically handle the state updates for the sequence such as by adding new messages to a chat history

# Reducer Function
# Rule that controls how updates from nodes are combined with the existing state
# Tells us how to merge new data into the current state
# without a reducer, updates would have replaced the existing value entirely!


#With out reducer:

# state={'messages':["hi"]}
# update={"messages":["how are you"]}
# new_state = {'messages':"how are you"}


# # With reducer:


# state={'messages':["hi"]}
# update={"messages":["how are you"]}
# new_state = {'messages':["hi""how are you"]}





class AgentState(TypedDict):
    messages:Annotated[Sequence[BaseMessage],add_messages]


@tool
def add(a:int,b:int):
    """This is an addition function that add two number together"""
    return a + b


tools=[add]

model=ChatGroq(model="llama-3.3-70b-versatile").bind_tools(tools)

def model_call(state:AgentState):
    system_prompt=SystemMessage(content=
                                "you are my AI assistant,please answer my query to the best of your ability."
                             )
    response=model.invoke([system_prompt] + state["messages"])
    return {"messages": [response]}

def should_continue(state:AgentState)->AgentState:
    messages=state['messages']
    last_message=messages[-1]
    if not last_message.tool_calls:
        return "end"
    else:
        return "continue"
    
graph = StateGraph(AgentState)
graph.add_node("our_agent",model_call)

tool_node=ToolNode(tools=tools)
graph.add_node("tools",tool_node)

graph.set_entry_point("our_agent")
graph.add_conditional_edges(
    "our_agent",
    should_continue,
    {
        "continue":"tools",
        "end":END,
    
    })

graph.add_edge("tools","our_agent")

app=graph.compile()
app

def print_stream(stream):
    for s in stream:
        message=s["messages"][-1]
        if isinstance(message,tuple):
            print(message)
        else:
            message.pretty_print()

inputs={'message':[{"user","Add 43 + 42"}]}

print_stream(app.stream(inputs,stream_mode="values"))


    
