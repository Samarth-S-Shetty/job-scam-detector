from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from tavily import TavilyClient
from typing import TypedDict
from dotenv import load_dotenv
import os

load_dotenv()
tavily=TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
llm=ChatGroq(model="llama-3.3-70b-versatile",api_key=os.getenv("GROQ_API_KEY"))

class StateAgent(TypedDict):
    company:str
    search_results:str
    red_flags:str
    scam_score:int
    email_content: str
    summary:str
print("setup ready!!!")

def search_node(state:StateAgent):
    company=state["company"]
    print(f"[search]searching for {company}")
    results=[]
    queries=[
            f"{company} official website",
            f"{company} reddit reviews",
            f"{company} scam complaints",
            f"{company} glassdoor reviews",
            f"{company} job experience employees"
    ]
    for querys in queries:
        result=tavily.search(querys)
        results.append(f"Query: {querys}\nResults: {str(result)}\n")
    combined="\n--\n".join(results)
    print(f"search done  found {len(results)}\n")
    return {"search_results":combined}
print("search_node ready!!!")

def analysis_node(state:StateAgent):
    print("[analysis] Analysis is starting ,search results is being sent to llm!!")
    print(f"[ANALYSIS] Search results length: {len(state['search_results'])} chars")
    print(f"[ANALYSIS] First 200 chars: {state['search_results'][:200]}")
    response=llm.invoke([
        SystemMessage(content="""You are a job scam detection expert.Analyze the search results and extract red flags that suggest this might be a scam.Look for: requests for money, vague job descriptions, too good to be true salaries,no physical address, bad reviews pattern, fake company signs.List each red flag clearly on a new line starting with '- """),
       HumanMessage(content=f"Analyze these search results for {state['company']}:\n{state['search_results']}")
    ])
    print(f"[ANALYSIS] Done. Red flags extracted.")
    return {"red_flags": response.content}


def scoring_node(state:StateAgent):
    response=llm.invoke([
        SystemMessage(content="""You are a scam scoring judge. Give a score 0-100.
100 = definite scam with clear evidence
0 = completely safe, well established company
50 = unknown company, insufficient information

Important rules:
- Well known companies (Google, Amazon, Microsoft etc) should score 0-10
- Established staffing firms with real addresses score 10-30
- Unknown companies with no online presence score 40-60
- Companies with actual scam reports score 70-100
- Lack of information alone is NOT enough for high score
- Only score high if there is ACTUAL evidence of scam activity

Reply with just the number."""),
        HumanMessage(content=f"Based on these red flags, give a scam score 0-100 for {state['company']}:\n{state['red_flags']}")
        
    ])
    try:
        score = int(response.content.strip())
    except:
        score = 50  # default if LLM returns something unexpected
    return {"scam_score": score}
print("[Scoring ]scoring done!!!")

def summary_node(state:StateAgent):
    response=llm.invoke([
        SystemMessage(content="""You are a job scam detection expert writing a final report.Write a clear, concise summary explaining:- Why the company got this scam score- The most important red flags found- A final recommendation (apply safely / proceed with caution / avoid)Keep it under 150 words."""),
       HumanMessage(content=f"Company: {state['company']}\nScam Score: {state['scam_score']}/100\nRed Flags:\n{state['red_flags']}")
    ])
    return {"summary":response.content}
    
def email_parser_node(state:StateAgent):
    print("[PARSER] Extracting company info from email...")
    
    response = llm.invoke([
        SystemMessage(content="""You are an email parser. Extract the following from the job email:
        1. Company name
        2. Job title
        3. Any suspicious elements in the email itself
        Return as plain text in this exact format:
        COMPANY: <company name>
        JOB: <job title>
        EMAIL_FLAGS: <any suspicious elements or 'none'>"""),
        HumanMessage(content=f"Parse this email:\n{state['email_content']}")
    ])
    
    # extract company name from response
    lines = response.content.split('\n')
    company = state["company"]  # fallback
    for line in lines:
        if line.startswith("COMPANY:"):
            company = line.replace("COMPANY:", "").strip()
    
    print(f"[PARSER] Extracted company: {company}")
    return {"company": company}



graph=StateGraph(StateAgent)
graph.add_node("email_node",email_parser_node)
graph.add_node("web_search",search_node)
graph.add_node("llm_node",analysis_node)
graph.add_node("score_node",scoring_node)
graph.add_node("summarizing_node",summary_node)

graph.set_entry_point("email_node")
graph.add_edge("email_node","web_search")
graph.add_edge("web_search","llm_node")
graph.add_edge("llm_node","score_node")
graph.add_edge("score_node","summarizing_node")
graph.add_edge("summarizing_node",END)

app = graph.compile()
print("graph ready")

if __name__ == "__main__":
    result = app.invoke({
        "company": "Vantage Point Consulting (VPC)",
        "search_results": "",
        "red_flags": "",
        "scam_score": 0,
        "summary": "",
        "email_content":"""Rahul Gautam <rgautam@vpc-staffing.com>
    20 May 2026, 21:31 (4 days ago)
    to me

    Hello,
    We have this immediate need with our client. Please look over the job description and send me your most updated resume and your expected rate as soon as you can.
    
    Job Title:   AI Architect
    Location:  Remote Job
    Duration:  12 Months+
    Job Overview:
    We are seeking a skilled AI Architect to design and implement scalable AI/ML solutions. The ideal candidate will have strong expertise in modern LLM frameworks and be capable of building intelligent, production-ready systems.
    Key Responsibilities:

    Design and architect end-to-end AI/ML solutions and pipelines.
    Develop and implement applications using LLM frameworks such as LangChain and LangGraph.
    Build and optimize AI workflows using tools like Strands and Fiddler.
    Collaborate with cross-functional teams to translate business requirements into AI-driven solutions.
    Ensure scalability, performance, and reliability of AI systems.
    Provide technical leadership and best practices for AI/ML development.
    Monitor and improve model performance and system efficiency.
    Required Skills & Experience:
    Strong experience in AI/ML and solution architecture.
    Hands-on expertise with LangChain, LangGraph, Strands, and Fiddler.
    Proficiency in Python and building AI/ML applications.
    Experience with LLMs, prompt engineering, and AI orchestration frameworks.
    Knowledge of model evaluation, monitoring, and governance.
    Strong problem-solving and communication skills.
    
    
    Warm Regards
    Rahul Gautam
    
    Technical Recruiter
    Vantage Point Consulting (VPC)
    Direct: +1 (470) 890 5908 | rgautam@vpc-staffing.com
    www.vpcstaffing.com
    5865 North Point Parkway, Ste 280, Alpharetta, GA 30022
    
    We make sure that all our services are developed within a designated time frame without compromising on quality. Connect with us today! Home – Vantage Point Consulting

    VPC DISCLAIMER: This e-mail transmission may contain confidential or legally privileged information that is intended only for the individual(s) or entity(ies) named in the e-mail address. If you are not the intended recipient, please reply so that arrangements can be made for proper delivery, and then please delete all copies and attachments. Any disclosure, copying, distribution, or reliance upon the contents of this e-mail, by any other than the intended recipients, is strictly prohibited.
    


    If you are interested in this position, please click here.

    If you would like to unsubscribe from Vantage Point Consulting, please click unsubscribe"""
    })

    print(f"\n--- SCAM SCORE: {result['scam_score']}/100 ---")
    print(f"\n--- RED FLAGS ---\n{result['red_flags']}")
    print(f"\n--- SUMMARY ---\n{result['summary']}")