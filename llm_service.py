# Everything that talks to an LLM lives here, so main.py can stay about HTTP.
#
# Two providers are supported: Gemini (free tier - what we develop against) and
# Claude. Set LLM_PROVIDER in .env to switch between them. Both are given the
# same Pydantic model from models.py as the response schema, so the rest of the
# app does not care which one is running.

import logging
import os

import anthropic
from dotenv import load_dotenv
from fastapi import HTTPException
from google import genai
from google.genai import errors as genai_errors

from models import ParsedCV, QuestionSet

logger = logging.getLogger(__name__)

# main.py also calls this, but it calls it *after* importing this module, so by
# then the settings below have already been read. Loading here as well means
# these pick up .env no matter what imports what first. load_dotenv is safe to
# call more than once.
load_dotenv()

PROVIDER = os.environ.get("LLM_PROVIDER", "gemini")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-opus-5")

_gemini_client = None
_claude_client = None


def get_gemini_client():
    # Clients are built on first use, not at import time, so the app still
    # starts (and /health still answers) when no API key is configured.
    global _gemini_client
    if _gemini_client is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise HTTPException(status_code=503, detail="GEMINI_API_KEY is not configured")
        _gemini_client = genai.Client(api_key=api_key)
    return _gemini_client


def get_claude_client():
    global _claude_client
    if _claude_client is None:
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise HTTPException(status_code=503, detail="ANTHROPIC_API_KEY is not configured")
        _claude_client = anthropic.Anthropic()
    return _claude_client


PARSER_PROMPT = """You extract structured information from CV text.

Rules:
- Only use information that actually appears in the CV. Do not invent anything.
- experience_years is total full-time professional experience, rounded down.
  Use 0 for students with no full-time job; internships do not count.
- If something is missing from the CV, use an empty string or an empty list."""


QUESTION_PROMPT = """You write interview questions for an HR interviewer.

Ground every question in the candidate's profile and the job role. Use a mix of
these four categories:
- verification: probe a specific claim on the CV
- technical: test real depth in a skill the role needs
- gap: something the role needs that the CV does not show
- behavioral: teamwork, conflict, ownership - lightly personalised to the CV

For each question also give a rubric. The rubric is NOT a model answer:
- strong_answer_covers: points a good answer would hit
- weak_answer_signs: what a weak or memorised answer looks like
- follow_up_probe: one follow-up the interviewer can ask

Write questions the interviewer can read out loud as they are."""


def call_gemini(system_prompt, user_message, output_model):
    try:
        response = get_gemini_client().models.generate_content(
            model=GEMINI_MODEL,
            contents=user_message,
            config={
                "system_instruction": system_prompt,
                "response_mime_type": "application/json",
                "response_schema": output_model,
            },
        )
    except genai_errors.APIError as e:
        if e.code == 429:
            raise HTTPException(status_code=429, detail="Gemini rate limit hit, try again shortly")
        logger.error(f"Gemini API returned {e.code}")
        raise HTTPException(status_code=502, detail="Gemini API request failed")

    if response.parsed is None:
        logger.error("Gemini did not return parsable JSON")
        raise HTTPException(status_code=502, detail="LLM did not return a usable response")

    usage = response.usage_metadata
    logger.info(
        f"Gemini call ok: model={GEMINI_MODEL} "
        f"in_tokens={usage.prompt_token_count} out_tokens={usage.candidates_token_count}"
    )
    return response.parsed


def call_claude(system_prompt, user_message, output_model):
    try:
        response = get_claude_client().messages.parse(
            model=CLAUDE_MODEL,
            max_tokens=16000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
            output_format=output_model,
        )
    except anthropic.RateLimitError:
        # RateLimitError subclasses APIStatusError, so it has to be caught first.
        raise HTTPException(status_code=429, detail="Claude rate limit hit, try again shortly")
    except anthropic.APIStatusError as e:
        logger.error(f"Claude API returned {e.status_code}")
        raise HTTPException(status_code=502, detail="Claude API request failed")
    except anthropic.APIConnectionError:
        raise HTTPException(status_code=503, detail="Could not reach the Claude API")

    # end_turn means Claude finished normally. Anything else (a refusal, or
    # running out of output tokens halfway through the JSON) is not usable.
    if response.stop_reason != "end_turn" or response.parsed_output is None:
        logger.error(f"Unusable Claude response, stop_reason={response.stop_reason}")
        raise HTTPException(status_code=502, detail="LLM did not return a usable response")

    logger.info(
        f"Claude call ok: model={CLAUDE_MODEL} "
        f"in_tokens={response.usage.input_tokens} out_tokens={response.usage.output_tokens}"
    )
    return response.parsed_output


def call_llm(system_prompt, user_message, output_model):
    if PROVIDER == "gemini":
        return call_gemini(system_prompt, user_message, output_model)
    if PROVIDER == "claude":
        return call_claude(system_prompt, user_message, output_model)
    raise HTTPException(status_code=500, detail=f"Unknown LLM_PROVIDER: {PROVIDER}")


def parse_cv(cv_text, job_role):
    user_message = f"Job role applied for: {job_role}\n\nCV text:\n{cv_text}"
    return call_llm(PARSER_PROMPT, user_message, ParsedCV)


def generate_questions(candidate, job_role, job_description, question_count):
    job_description = job_description or "(not provided - use the job role only)"
    user_message = (
        f"Job role: {job_role}\n\n"
        f"Job description:\n{job_description}\n\n"
        f"Candidate profile, already parsed from their CV:\n"
        f"{candidate.model_dump_json(indent=2)}\n\n"
        f"Write exactly {question_count} questions covering all four categories."
    )
    return call_llm(QUESTION_PROMPT, user_message, QuestionSet)
