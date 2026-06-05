"""Prompt templates for Claude caption generation."""

from __future__ import annotations

from app.enums import Platform
from app.pipeline.ingestion.base import RawArticle

SYSTEM_PROMPT = """You are an experienced public-relations social media manager. \
You write engaging, factual, on-brand social posts based on news about the PR and \
communications industry. You never use clickbait, never fabricate facts, and keep \
an upbeat, professional voice. You respond only with valid JSON."""

PLATFORM_GUIDANCE: dict[Platform, str] = {
    Platform.INSTAGRAM: (
        "Target Instagram. Caption up to ~2200 characters but keep it punchy. "
        "Include 3-8 relevant hashtags. A line break or two is welcome."
    ),
    Platform.FACEBOOK: (
        "Target a Facebook Page. Keep the caption under ~600 characters for "
        "engagement. Use at most 1-2 hashtags."
    ),
}


def build_user_prompt(article: RawArticle, platform: Platform) -> str:
    guidance = PLATFORM_GUIDANCE.get(platform, "")
    return f"""Write a social media post about this article.

Title: {article.title}
Source: {article.domain}
Summary: {article.snippet or "(no summary available)"}

{guidance}

Respond with JSON only, in exactly this shape:
{{
  "caption": "the post text (no surrounding quotes)",
  "hashtags": ["tag1", "tag2"],
  "image_query": "2-4 word search phrase for a relevant stock photo"
}}"""
