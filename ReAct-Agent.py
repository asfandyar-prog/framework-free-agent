import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from Agentic.tools import search_wikipedia

load_dotenv()

class Agent:
    def __init__(self):
        self.memory=[]
        self.previous_action=[]
        self.searched=False
        self.llm=ChatGroq(
        model_name="llama-3.3-70b-versatile",
        groq_api_key=os.getenv("GROQ_API_KEY")
    )
        self.tools = {
    "search_wikipedia": search_wikipedia
}



    
    # Define the llm
    


    def call_llm(self,prompt:str):
        """Call the LLM and return the response."""
        try:
            response=self.llm.invoke(prompt)
            return response.content
        except Exception as e:
            return f"Error: {str(e)}"

    def parse_response(self,response: str):
        lines = response.split("\n")
        thought = ""
        action = ""
        action_input = ""

        for line in lines:
            if line.startswith("Thought:"):
                thought = line.replace("Thought:", "").strip()
            elif line.startswith("Action:"):
                action = line.replace("Action:", "").strip()
            elif line.startswith("Action Input:"):
                action_input = line.replace("Action Input:", "").strip()

        return thought, action, action_input

    def build_prompt(self,question:str):
        base_prompt = """
        you are autnomus agent 
        you must respond in this format:
        

        Thought : your reasoning
        Action : search_wikipedia | finish
        Action Input : input for the action
        Rule : You must call search_wikipedia at least once before finish.

        """
        memory_block =""

        for step in self.memory:
            memory_block +=f"""
            Thought: {step['thought']}
            Action: {step['action']}
            Action Input: {step['input']}
            Observation: {step['observation']}
            """

        return base_prompt + f"\nQuestion: {question}\n" + memory_block




    def execute_action(self,action,action_input):
        """Execute the action and return the observation."""
        allowed_actions=set(self.tools.keys())|{"finish"}
        if action not in allowed_actions:
            return f"Error: Invalid action {action}. Allowed actions are {allowed_actions}"
        if action == "finish":
            if not self.searched:
                observation = "You must call search_wikipedia atleast once before finishing"
        return "FINISH"
        
        observation = self.tools[action](action_input)
        if "Error" not in observation and observation != "No result found.":
            self.searched = True
        return observation

    def reflect(self, question, thought, action, action_input, observation):

    # Special handling for FINISH
        if action == "finish":
                        reflection_prompt = f"""
            You are reviewing the final answer of an autonomous agent.

            Question: {question}            
            Proposed Final Answer: {action_input}

            Does this fully and correctly answer the question?

            If the answer is incomplete, vague, or does not directly answer the question,
            respond with: REVISE

            If the answer clearly and directly answers the question,
            respond with: CONTINUE

            Respond with only one word: CONTINUE or REVISE.
            """
        else:
            reflection_prompt = f"""
            You are reviewing the last reasoning step of an autonomous agent.

            Question: {question}        

            Last Thought: {thought}
            Last Action: {action}
            Last Action Input: {action_input}
            Last Observation: {observation}

            Was this action helpful and logically progressing toward solving the question?

            Respond with only one word:
            CONTINUE or REVISE
            """

        response = self.call_llm(reflection_prompt)

        if "REVISE" in response.upper():
            return "revise"

        return "continue"


    def run_agent(self,question: str, max_steps=5):
        self.memory=[]
        self.searched=False
        self.previous_action=[]
        
        for step in range(max_steps):
            prompt = self.build_prompt(question)
            response = self.call_llm(prompt)
            print("\nLLM Response:\n", response)

            thought, action, action_input = self.parse_response(response)
            if not thought or not action or not action_input:
                observation = "Format error. You must respond with Thought,Action,Action Input."
                self.memory.append({
                    "thought": thought,
                    "action": action,
                    "input": action_input,
                    "observation": observation
                })      
                continue

            current_pair=(action,action_input)
            if current_pair in self.previous_action:
                print("\nError: Infinite loop detected. Repeating previous action.")
                return "Error: Infinite loop detected."
            self.previous_action.append(current_pair)

            observation = self.execute_action(action, action_input)

            # If finish, reflect first before returning
            if observation == "FINISH":
                decision = self.reflect(question, thought, action, action_input, observation)

                if decision == "revise":
                    print("\nReflection: REVISE final answer")
                    continue

                print("\nFinal Answer:", action_input)
                return action_input

            # For normal tool actions
            decision = self.reflect(question, thought, action, action_input, observation)

            if decision == "revise":
                print("\nReflection: REVISE step")
                continue    

            print(f"Step {step+1}")
            print(f"Thought: {thought}")
            print(f"Action: {action}")
            print(f"Action Input: {action_input}")
        print(f"Observation: {observation}")

        observation = observation[:1000]

        self.memory.append({
            "thought": thought,
            "action": action,
            "input": action_input,
                "observation": observation
            })

        print("Max steps reached.")

