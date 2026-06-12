"""
NepHub AI Writer — admin-only.

Takes raw input (screenshot, PDF, pasted text, or a URL), sends it to the
Claude API, and returns a clean, structured job draft ready to prefill
the admin job form.

Requires ANTHROPIC_API_KEY in the environment. Model can be overridden
with WRITER_MODEL (defaults to claude-sonnet-4-6).
"""

import base64
import json
import os
import re

import requests as http_requests

# Tool schema forces Claude to return exactly the fields our Job form needs.
JOB_DRAFT_TOOL = {
    "name": "save_job_draft",
    "description": "Save the extracted and professionally rewritten job posting draft.",
    "input_schema": {
        "type": "object",
        "properties": {
            "title":            {"type": "string", "description": "Clear, professional job/opportunity title. No ALL CAPS."},
            "organization":     {"type": "string", "description": "Hiring organisation or provider name."},
            "category": {
                "type": "string",
                "enum": ["government", "loksewa", "private", "scholarship", "foreign", "internship", "opportunity"],
                "description": "Best-fit NepHub category. Loksewa = Public Service Commission Nepal. Foreign = jobs abroad for Nepalis. Opportunity = fellowships/trainings/competitions.",
            },
            "job_type": {
                "type": "string",
                "enum": ["full_time", "part_time", "contract", "internship", ""],
            },
            "experience_level": {
                "type": "string",
                "enum": ["entry", "mid", "senior", "any"],
            },
            "location": {
                "type": "string",
                "enum": ["koshi", "madhesh", "bagmati", "gandaki", "lumbini", "karnali", "sudurpashchim", "remote", "nepal"],
                "description": "Nepal province if determinable, 'remote' for WFH, otherwise 'nepal'. For foreign jobs use 'nepal'.",
            },
            "description": {
                "type": "string",
                "description": "Professional, well-structured description (2-5 short paragraphs). Plain text, no markdown headers. Write it properly even if the source is messy or in Nepali — translate to clear English.",
            },
            "requirements": {
                "type": "string",
                "description": "Qualifications/requirements, one per line. Plain text.",
            },
            "deadline": {
                "type": "string",
                "description": "Application deadline as YYYY-MM-DD. If the source uses a Bikram Sambat (BS) date, convert to AD. Empty string if no deadline found.",
            },
            "apply_link": {"type": "string", "description": "Official application URL if present, else empty string."},
            "source":     {"type": "string", "description": "Source website/organisation domain if identifiable, else empty string."},
            "salary_min": {"type": "integer", "description": "Minimum monthly salary in NPR, 0 if unknown."},
            "salary_max": {"type": "integer", "description": "Maximum monthly salary in NPR, 0 if unknown."},
            "confidence_notes": {
                "type": "string",
                "description": "1-3 short bullet points for the admin: anything uncertain, guessed, or needing manual verification (e.g. 'Deadline converted from BS — please verify').",
            },
        },
        "required": ["title", "organization", "category", "description", "confidence_notes"],
    },
}

SYSTEM_PROMPT = """You are the in-house content writer for NepHub, Nepal's job portal.
An admin gives you raw material about a job, internship, scholarship, or opportunity —
a screenshot, PDF, messy pasted text (possibly in Nepali), or scraped webpage text.

Your job:
1. Extract every fact available.
2. Rewrite it as a clean, professional NepHub listing in clear English.
3. Pick the correct category, province, job type, and experience level.
4. Convert Nepali (Bikram Sambat) dates to AD dates. BS year minus 56 years 8.5 months ≈ AD; e.g. 2082 Ashadh ≈ June/July 2025.
5. Never invent facts. If salary, deadline, or links are not in the source, leave them empty/0.
6. Flag anything uncertain in confidence_notes so the admin can verify before publishing.

Always call the save_job_draft tool with your result."""


class WriterError(Exception):
    """Raised with a human-readable message for the admin UI."""


def _get_client():
    api_key = os.environ.get('ANTHROPIC_API_KEY', '')
    if not api_key:
        raise WriterError(
            'ANTHROPIC_API_KEY is not set. Add it in Railway Variables '
            '(get a key at console.anthropic.com).'
        )
    try:
        import anthropic
    except ImportError:
        raise WriterError('The "anthropic" package is not installed.')
    return anthropic.Anthropic(api_key=api_key)


def _fetch_url_text(url):
    """Best-effort fetch of a job posting URL. Some sites (LinkedIn) block bots."""
    try:
        resp = http_requests.get(url, timeout=15, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        })
        resp.raise_for_status()
    except Exception as exc:
        raise WriterError(
            f'Could not fetch that URL ({exc}). LinkedIn and some sites block bots — '
            'take a screenshot of the posting and upload that instead.'
        )
    html = resp.text
    # crude but dependency-free html → text
    html = re.sub(r'<(script|style|noscript)[^>]*>.*?</\1>', ' ', html, flags=re.S | re.I)
    text = re.sub(r'<[^>]+>', ' ', html)
    text = re.sub(r'\s+', ' ', text).strip()
    if len(text) < 200:
        raise WriterError(
            'That page returned almost no readable text (probably bot-protected). '
            'Upload a screenshot of the posting instead.'
        )
    return text[:60000]


def extract_job_draft(*, uploaded_file=None, pasted_text='', url=''):
    """
    Returns dict with the job draft fields + 'confidence_notes'.
    Exactly one of uploaded_file / pasted_text / url should be provided;
    if several are given, all are included as context.
    """
    content = []

    if uploaded_file is not None:
        data = uploaded_file.read()
        if len(data) > 20 * 1024 * 1024:
            raise WriterError('File too large (max 20 MB).')
        ctype = (uploaded_file.content_type or '').lower()
        b64 = base64.standard_b64encode(data).decode()
        if ctype == 'application/pdf':
            content.append({
                "type": "document",
                "source": {"type": "base64", "media_type": "application/pdf", "data": b64},
            })
        elif ctype in ('image/jpeg', 'image/png', 'image/gif', 'image/webp'):
            content.append({
                "type": "image",
                "source": {"type": "base64", "media_type": ctype, "data": b64},
            })
        else:
            raise WriterError('Unsupported file type. Upload a PDF, JPG, PNG, GIF or WebP.')

    if url.strip():
        page_text = _fetch_url_text(url.strip())
        content.append({"type": "text",
                        "text": f"Scraped text from {url.strip()}:\n\n{page_text}"})

    if pasted_text.strip():
        content.append({"type": "text",
                        "text": f"Raw text from admin:\n\n{pasted_text.strip()[:60000]}"})

    if not content:
        raise WriterError('Give me something to work with — a file, some text, or a URL.')

    content.append({
        "type": "text",
        "text": "Extract and professionally rewrite this as a NepHub listing. Call save_job_draft.",
    })

    client = _get_client()
    model = os.environ.get('WRITER_MODEL', 'claude-sonnet-4-6')

    try:
        response = client.messages.create(
            model=model,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=[JOB_DRAFT_TOOL],
            tool_choice={"type": "tool", "name": "save_job_draft"},
            messages=[{"role": "user", "content": content}],
        )
    except Exception as exc:
        raise WriterError(f'Claude API error: {exc}')

    for block in response.content:
        if block.type == 'tool_use' and block.name == 'save_job_draft':
            draft = dict(block.input)
            # sanitise
            if draft.get('deadline') and not re.match(r'^\d{4}-\d{2}-\d{2}$', draft['deadline']):
                draft['confidence_notes'] = (
                    draft.get('confidence_notes', '') +
                    f"\n• Deadline '{draft['deadline']}' was not a valid date — left blank, set it manually."
                ).strip()
                draft['deadline'] = ''
            for k in ('salary_min', 'salary_max'):
                try:
                    draft[k] = int(draft.get(k) or 0)
                except (TypeError, ValueError):
                    draft[k] = 0
            return draft

    raise WriterError('Claude did not return a structured draft. Try again.')
