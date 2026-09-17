import os
from pydantic import BaseModel, Field
from agents import Agent, Runner, WebSearchTool

MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")

class ResearchPack(BaseModel):
    topic: str
    angle: str
    key_facts: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)

class StoryPack(BaseModel):
    hook: str
    script: str
    scene_text: list[str] = Field(default_factory=list)
    title: str
    description: str
    tags: list[str] = Field(default_factory=list)

class QAPack(BaseModel):
    passed: bool
    issues: list[str] = Field(default_factory=list)
    fixes: list[str] = Field(default_factory=list)

researcher = Agent(
    name="Florexia Researcher",
    model=MODEL,
    instructions="""You are Florexia, the research lead of NOIR//NULL. You have a feminine, warm, sharp presentation style, but you are an AI. Research the requested topic using web search. Prefer primary sources and reputable reporting. Never invent citations. Separate verified facts from uncertain claims. Return concise evidence a script writer can use.""",
    tools=[WebSearchTool()],
    output_type=ResearchPack,
)

storyteller = Agent(
    name="Florexia Story Director",
    model=MODEL,
    instructions="""You are Florexia's story director. Turn research into an original faceless YouTube Short or documentary segment. Use hook -> question -> discovery -> explanation -> twist -> takeaway. Write clear Hinglish. Do not fabricate facts. scene_text should contain short on-screen lines. Create title, description and tags.""",
    output_type=StoryPack,
)

qa = Agent(
    name="Florexia QA Editor",
    model=MODEL,
    instructions="""You are final editorial QA. Check factual support, unsupported claims, repetitive/mass-produced feel, misleading wording, unsafe instructions, and whether the script explains something. Pass only when publishable after normal production QA. Give concrete fixes.""",
    output_type=QAPack,
)

async def run_pipeline(topic: str, kind: str = "short"):
    research = await Runner.run(researcher, f"Research this topic for a {kind}: {topic}")
    rp = research.final_output
    story = await Runner.run(storyteller, f"Topic: {topic}\nType: {kind}\nResearch:\n{rp.model_dump_json()}")
    sp = story.final_output
    check = await Runner.run(qa, f"Research:\n{rp.model_dump_json()}\nDraft:\n{sp.model_dump_json()}")
    qp = check.final_output
    if not qp.passed:
        repaired = await Runner.run(storyteller, f"Repair the draft using QA issues. Topic: {topic}\nResearch: {rp.model_dump_json()}\nDraft: {sp.model_dump_json()}\nQA: {qp.model_dump_json()}")
        sp = repaired.final_output
        check2 = await Runner.run(qa, f"Research:\n{rp.model_dump_json()}\nDraft:\n{sp.model_dump_json()}")
        qp = check2.final_output
    return rp, sp, qp
