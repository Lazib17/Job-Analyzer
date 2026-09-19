"""
Google AI Studio (Gemini) integration for job-resume analysis.
"""

import json
import logging
import re
from typing import Optional

import google.generativeai as genai

from config import settings
from models.analysis import AIAnalysisResult

logger = logging.getLogger(__name__)

ANALYSIS_SYSTEM_PROMPT = """You are an expert career coach and technical recruiter.
Analyze job listings against candidate resumes with precision and fairness.
Always respond with valid JSON only — no markdown, no code fences, no extra text."""

ANALYSIS_USER_PROMPT = """Analyze the following candidate resume and job description.

Return a JSON object with exactly these fields:
- compatibility_score (integer 0-100)
- matching_skills (array of strings)
- missing_skills (array of strings)
- improvement_suggestions (string with actionable advice)
- explanation (short string explaining why the job is or isn't a good fit)

## Candidate Resume
{resume_text}

## Job Title
{job_title}

## Company
{company}

## Job Description
{description}

## Requirements
{requirements}
"""


class GoogleAIService:
    """Service wrapper for Google AI Studio (Gemini) job analysis."""

    def __init__(self):
        if not settings.google_api_key:
            logger.warning("GOOGLE_API_KEY not set — analysis will fail.")
        else:
            genai.configure(api_key=settings.google_api_key)
        self.model_name = settings.google_model
        self.fallback_models = [
            settings.google_model,
            "gemini-1.5-flash",
            "gemini-2.0-flash-lite",
            "gemini-1.5-flash-8b",
        ]

    def _get_model(self, model_name: str) -> genai.GenerativeModel:
        return genai.GenerativeModel(
            model_name=model_name,
            system_instruction=ANALYSIS_SYSTEM_PROMPT,
        )

    def _generate_with_fallback(self, prompt: str) -> str:
        """Try primary model, then fallbacks on quota errors."""
        seen: set[str] = set()
        last_error: Optional[Exception] = None

        for model_name in self.fallback_models:
            if model_name in seen:
                continue
            seen.add(model_name)
            try:
                model = self._get_model(model_name)
                response = model.generate_content(
                    prompt,
                    generation_config=genai.GenerationConfig(
                        temperature=0.3,
                        max_output_tokens=1024,
                        response_mime_type="application/json",
                    ),
                )
                return response.text or ""
            except Exception as exc:
                last_error = exc
                err = str(exc).lower()
                if "429" in err or "quota" in err or "resourceexhausted" in err:
                    logger.warning("Model %s quota exceeded, trying fallback...", model_name)
                    continue
                raise

        if last_error:
            raise last_error
        raise RuntimeError("No Gemini models available")

    def _parse_json_response(self, text: str) -> dict:
        """Extract JSON from model response, handling markdown fences."""
        cleaned = text.strip()
        fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
        if fence_match:
            cleaned = fence_match.group(1)
        return json.loads(cleaned)

    async def analyze_job(
        self,
        resume_text: str,
        job_title: str,
        company: str,
        description: str,
        requirements: Optional[str] = None,
    ) -> AIAnalysisResult:
        """Send resume + job data to Gemini and return structured analysis."""
        prompt = ANALYSIS_USER_PROMPT.format(
            resume_text=resume_text[:8000],
            job_title=job_title,
            company=company,
            description=description or "Not provided",
            requirements=requirements or "Not specified",
        )

        try:
            raw_text = self._generate_with_fallback(prompt)
            parsed = self._parse_json_response(raw_text)
            return AIAnalysisResult(**parsed)
        except json.JSONDecodeError as exc:
            logger.error("Failed to parse Gemini JSON response: %s", exc)
            raise ValueError("Gemini returned invalid JSON. Please retry.") from exc
        except Exception as exc:
            logger.error("Google AI error: %s", exc)
            raise


# Singleton instance
google_ai_service = GoogleAIService()
