"""Interactive command-line interface."""

from pydantic import ValidationError

from app.models import ResearchRequest
from app.orchestrator import run_research


async def start_cli() -> None:
    print("FirstAidOps - type 'exit' to stop")
    while True:
        question = input("\nYour question: ").strip()
        if question.casefold() in {"exit", "quit"}:
            return
        try:
            request = ResearchRequest(question=question)
        except ValidationError as exc:
            print(f"Invalid question: {exc.errors()[0]['msg']}")
            continue
        draft = await run_research(request.question, approved_to_save=False)
        print(f"\n--- Draft ---\n{draft.result}")
        approval = input("\nApprove saving a report? [y/N]: ").strip().casefold()
        if approval == "y":
            final = await run_research(request.question, approved_to_save=True)
            print(f"\n--- Approved Result ---\n{final.result}")
        else:
            print("No report was saved.")
