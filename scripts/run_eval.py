"""
Manual eval run script.
Run this to score the RAG system against the held-out question set.

Usage:
    cd backend
    python -m scripts.run_eval
"""
import asyncio
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

from eval.ragas_eval import run_eval_suite
from config import settings


async def main():
    print("\n=== HealthSignal RAGAS Eval Run ===\n")
    results = await run_eval_suite()

    if "error" in results:
        print(f"ERROR: {results['error']}")
        return

    print(f"Questions evaluated : {results.get('n', 0)}")
    print(f"Avg Faithfulness    : {results.get('avg_faithfulness', 0):.3f}")
    print(f"Avg Answer Relevancy: {results.get('avg_answer_relevancy', 0):.3f}")
    print(f"Avg Context Recall  : {results.get('avg_context_recall', 0):.3f}")
    print(f"Threshold           : {settings.ragas_faithfulness_threshold}")

    faith = results.get("avg_faithfulness", 0)
    if faith < settings.ragas_faithfulness_threshold:
        print(f"\n⚠️  BELOW THRESHOLD — faithfulness {faith:.3f} < {settings.ragas_faithfulness_threshold}")
    else:
        print(f"\n✅ Faithfulness PASSING ({faith:.3f} >= {settings.ragas_faithfulness_threshold})")


if __name__ == "__main__":
    asyncio.run(main())
