import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from backend.llm import generate_tier_b, grounded_qa

async def main():
    print("--- FRANCE TEST ---")
    tier_b_res = await generate_tier_b(
        jurisdiction_ref=None,
        jurisdiction_name="France",
        clauses_json="[]"
    )
    import json
    print(json.dumps(tier_b_res, indent=2))
    
    print("\n--- QA TEST 1 ---")
    qa_1 = await grounded_qa(
        question="Is my landlord allowed to evict me for no reason?",
        document_text="This is a residential lease.",
        jurisdiction_ref=None,
        chat_history=[]
    )
    print(qa_1["answer"])
    
    print("\n--- QA TEST 2 ---")
    qa_2 = await grounded_qa(
        question="Can I sue my landlord for this?",
        document_text="This is a residential lease.",
        jurisdiction_ref=None,
        chat_history=[]
    )
    print(qa_2["answer"])

if __name__ == "__main__":
    asyncio.run(main())
