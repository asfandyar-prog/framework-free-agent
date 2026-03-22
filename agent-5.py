from typing import TypedDict,Annotated,Sequence
from langgraph.graph import StateGraph,START,END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from langchain_core.messages import BaseMessage,HumanMessage,AIMessage,ToolMessage,SystemMessage

load_dotenv()

# This is the global variable to store document content

document_content=""

class AgentState(TypedDict):
    messages:Annotated[Sequence[BaseMessage],add_messages]

@tool
def update(content:str)->str:
    """Updates the document with the provided content"""

    global document_content
    document_content=content


    return f"Document has been updated successfully! the current content is :\n{document_content} "

@tool 
def save(filename:str)->str:
    """Save teh current document to a text file and finish the process.

    Args:
        filename:Name for the text file.

    """

    global document_content
    if not filename.endswith(".txt"):
        filename=f"{filename}.txt"

    try :
        with open(filename,"w") as file:
            file.write(document_content)
        print(f"\n Document has been saved to :{filename}")
        return f"Document has been saved successfully to '{filename}'."
    except Exception as e:
        return f"Error savign document: {str(e)}"
    
tools = [update,save]

model=ChatGroq(model="llama-3.3-70b-versatile").bind_tools(tools)

def our_agent(state:AgentState)->AgentState:
    system_prompt=SystemMessage(content=f"""

    You are Drafter, a helpful writting assistent. You are going to help user with updating and saving the following:
        - if the user wants to update or modify the content, use the 'update' tool with the complete   update content
        - if the user wants to save and finish the process you need to use the 'save' tool.
        -   make sure to allow show the current document state after modificaitons.

    The current document content is : {document_content}                                             
                               
 """)
    
    if not state['messages']:
        user_input="I'm ready to help you update a document.What would you like to create?"
        user_message=HumanMessage(content=user_input)
    
    else:
        user_input=input("\n What would you like to do with the document?")
        print(f"\n USER: {user_input}")
        user_message=HumanMessage(content=user_input)

    all_message=[system_prompt]+list(state["messages"]) + [user_message]


    response=model.invoke(all_message)

    print(f"\n Ai: {response.content}")
    if hasattr(response,"tool_calls") and response.tool_calls:
        print(f" USING TOOLS : {[tc["name"] for tc in response.tool_calls]}")
    
    return {"messages": list(state["messages"])+ [user_message,response]}

def should_countinue(state:AgentState)->AgentState:
    """Determine if we should continue or end the conversation."""
    messages=state['messages']

    if not messages:
        return "continue"
    # this looks for the most recent tool message....
    for message in reversed(messages):
        # ... and checks if tis is  a toolmessage resulting from save
        if (isinstance(message,ToolMessage) and
            "saved" in message.content.lower()and
            "document" in message.content.lower()):
            return "end"
        
        return "continue"
    
def print_message(messages):
    """Function I made to print the messages in a more readable format"""
    if not messages:
        return
    for message in messages[-3:]:
        if isinstance(message,ToolMessage):
            print(f"\n TOOL RESULT : {message.content}")



graph=StateGraph(AgentState)
graph.add_node("agent",our_agent)
graph.add_node("tools",ToolNode(tools))

    
graph.set_entry_point("agent")


graph.add_edge("agent","tools")
graph.add_conditional_edges(
    "tools",
    should_continue,
    {
        "continue":"agent",
        "end":END
    },
)

app=graph.compile()



def run_document_agent():
    print("\n ===== Drafter =====")
    state={"messages": []}
    for step in app.stream(state,stream_mode="values"):
        if "messages" in step:
            print_messages(step["messages"])
    print(f"\n === Drift Finish ===")
