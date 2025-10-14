# routes/utils/ai_arbiter.py

import asyncio
import base64
import json
import os
from typing import Any, Dict, List

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
env_path = os.path.join(project_root, ".env")
load_dotenv(env_path)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


# Placeholder for actual API calls to an LLM provider (e.g., OpenAI)
async def call_gpt_api(system: str, prompt: str, output_structure: object):
    """Placeholder for a real GPT-4 call. Returns a mock response."""
    response = await asyncio.to_thread(
        client.responses.parse,
        model="gpt-5",
        input=[
            {"role": "system", "content": system},
            {
                "role": "user",
                "content": prompt,
            },
        ],
        text_format=output_structure,
    )
    return response.output_parsed


async def call_gpt_vision_api(
    prompt: str, image_paths: List[str], output_structure: object
) -> Dict[str, Any]:
    """Placeholder for a real GPT-4 Vision call."""
    content = []
    for path in image_paths:
        base64_image = encode_image(path)
        content.append(
            {
                "type": "input_image",
                "image_url": f"data:image/jpeg;base64,{base64_image}",
            }
        )

    response = await asyncio.to_thread(
        client.responses.parse,
        model="gpt-5",
        input=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": content},
        ],
        text_format=output_structure,
    )
    return response.output_parsed


EVIDENCE_REQUIREMENTS = {
    "DIGITAL_GOODS": ["file_upload", "screenshot_of_deliverable"],
    "SERVICES_TIMED": ["calendar_proof", "both_parties_confirmation_messages"],
    "SERVICES_DELIVERABLE": ["completed_work_upload", "acceptance_communication"],
    "SOCIAL_PROOF": ["public_link_to_post", "screenshot_with_timestamp"],
}


class TransactionClassifier:
    async def classify(self, transaction_description: str) -> Dict[str, Any]:
        class Transaction(BaseModel):
            category: str

        system_prompt = f"""
            You are a precise transaction classifier for an escrow service.

            Your task is to analyze the following transaction description and classify it into ONE of the predefined categories.

            ## Predefined Categories ##
            - DIGITAL_GOODS
            - SERVICES_TIMED
            - SERVICES_DELIVERABLE
            - SOCIAL_PROOF
            - PHYSICAL_GOODS

            Based on your analysis, return ONLY a single, raw JSON object with one key, "category", containing the chosen category as a string.

            Do not include any introductory text, explanation, or markdown formatting like ```json.
        """
        user_prompt = transaction_description
        response = await call_gpt_api(system_prompt, user_prompt, Transaction)
        # Add static requirements for the classified category

        response_dict = response.model_dump()

        # Add static requirements for the classified category
        response_dict["required_evidence"] = EVIDENCE_REQUIREMENTS.get(
            response_dict.get("category"), []
        )
        return response_dict


class AIVerifier:
    async def verify_evidence(
        self, transaction_details: Dict, evidence_bundle: Dict
    ) -> Dict[str, Any]:
        """Multi-step verification process using your proposed logic."""

        verification_results = []
        # --- Image Verification ---
        if evidence_bundle:
            image_paths = [
                os.path.join(project_root, "uploads", path)
                for path_list in evidence_bundle.values()
                for path in path_list
            ]

            image_analysis = await self._verify_images(image_paths, transaction_details)
            verification_results.append(image_analysis)

        # --- Final Synthesis ---
        final_decision = await self._cross_verify_all_evidence(
            verification_results, transaction_details
        )
        return final_decision.model_dump()

    async def _verify_images(
        self, image_paths: List[str], details: Dict
    ) -> Dict[str, Any]:
        class ImageVerifier(BaseModel):
            confidence: str
            reasoning: str
            red_flags: list[str]

        prompt = f"""
            You are a digital evidence analyst specializing in visual verification for escrow disputes.

            Your task is to analyze the provided image(s) to determine if they constitute proof of delivery for the following transaction.

            ## Transaction Details ##
            Description: "{details}"

            ## Analysis Criteria ##
            Your analysis must address the following points:
            1.  **Deliverable Match:** Does the content of the image(s) directly correspond to the promised deliverable (e.g., a logo, a screenshot of a completed task)?
            2.  **Authenticity:** Are there signs of authenticity, such as legitimate UI elements, timestamps, or context? Conversely, are there any signs of digital manipulation, cropping to hide information, or fraud?
            3.  **Quality:** Does the quality of the work shown in the image appear to match what would be reasonably expected for the transaction?

            ## Required Output ##
            Based on your analysis, return ONLY a single, raw JSON object with the following structure:
            - "confidence": A float from 0.0 (no proof) to 1.0 (undeniable proof) that the image(s) prove delivery.
            - "reasoning": A concise, one-sentence explanation for your confidence score.
            - "red_flags": A JSON array of strings, listing any specific concerns or signs of manipulation you identified. If none, return an empty array.

            Do not include markdown or any other text.        
        """
        return await call_gpt_vision_api(prompt, image_paths, ImageVerifier)

    async def _cross_verify_all_evidence(
        self, results: List[Dict], details: Dict
    ) -> Dict[str, Any]:
        class FinalDecision(BaseModel):
            decision: str
            final_confidence: float
            reasoning: str
            summary_of_evidence: str

        prompt = f"""
            You are the final AI Escrow Arbiter. Your decision is binding. You must be impartial, analytical, and base your decision solely on the evidence provided.

            ## Transaction Details ##
            Description: "{details["description"]}"
            Amount: ${details["amount"]}

            ## Summarized Evidence Analysis ##
            {results}

            ## Decision Framework ##
            You MUST follow this strict framework to reach your decision:
            1.  Review all provided evidence analyses for their confidence scores and red flags.
            2.  Calculate an aggregate confidence score. Give more weight to high-quality, direct evidence (e.g., verified deliverables) and less weight to circumstantial evidence (e.g., chat logs).
            3.  **If the final aggregate confidence score is greater than 0.75, your decision MUST be "APPROVE".**
            4.  **If the final aggregate confidence score is 0.75 or less, your decision MUST be "REJECT".**

            ## Required Output ##
            Your response must be ONLY a single, raw JSON object with the following structure:
            - "decision": The final binding decision, either "APPROVE" (release to seller) or "REJECT" (refund buyer).
            - "final_confidence": The final aggregate confidence score (float from 0.0 to 1.0).
            - "reasoning": A detailed, multi-sentence explanation for your decision, referencing specific pieces of evidence and how they contributed to the final confidence score.
            - "summary_of_evidence": A brief summary of the strongest piece of evidence for the seller and the strongest point for the buyer.

            Do not include any text outside of the JSON object.
        """
        return await call_gpt_api(prompt, "", FinalDecision)


if __name__ == "__main__":

    async def main():
        # --- 1. Define the Test Data ---
        # This simulates the data that would be pulled from your `Room` model.

        transaction_details = {
            "description": (
                "I need a professional logo for my new YouTube channel, 'RetroReplay'. "
                "The logo must be in a pixel art style, reminiscent of 16-bit SNES games. "
                "It should feature a vintage game controller and use a specific color palette: "
                "deep purple, neon pink, and electric blue. The final deliverable should be a "
                "high-resolution PNG file with a transparent background."
            ),
            "amount": 150.0,
        }

        # This simulates the evidence submitted by the seller.
        # It uses the local file paths for the images you just created.
        evidence_bundle = {
            "screenshot_of_deliverable": [
                "test_workspace.png",
                "test_logo.png",  # The "proof of work" screenshot
            ],
        }

        print("--- Starting AI Verification Demo ---")
        print(f"Transaction: {transaction_details['description']}")
        print(f"Evidence Submitted: {evidence_bundle}")
        print("-" * 35)

        # --- 2. Instantiate and Run the Verifier ---
        # This is the main entry point for the dispute resolution process.

        verifier = AIVerifier()
        final_verdict = await verifier.verify_evidence(
            transaction_details, evidence_bundle
        )

        # --- 3. Print the Final Result ---
        # This will show the final JSON object from the arbiter.

        print("\n--- AI ARBITER FINAL VERDICT ---")
        # Pretty-print the final JSON decision
        print(json.dumps(final_verdict, indent=2))
        print("-" * 35)

    # Run the asynchronous main function
    asyncio.run(main())
