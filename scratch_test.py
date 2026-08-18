import os
from dotenv import load_dotenv
load_dotenv()
from crewai import LLM, Agent, Task, Crew

def test_model(model_name):
    print(f"Testing {model_name}...")
    try:
        llm = LLM(model=model_name, api_key=os.getenv("GEMINI_API_KEY"))
        agent = Agent(role="Test", goal="Test", backstory="Test", llm=llm)
        task = Task(description="Say hello", expected_output="A greeting", agent=agent)
        crew = Crew(agents=[agent], tasks=[task])
        crew.kickoff()
        print(f"Success {model_name}!")
    except Exception as e:
        print(f"Failed {model_name}: {str(e)}")

test_model("gemini/gemini-1.5-flash")
test_model("gemini/gemini-1.5-flash-latest")
test_model("gemini/gemini-2.5-flash")
test_model("gemini/gemini-flash-latest")
