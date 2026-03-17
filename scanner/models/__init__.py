"""
Analysis models for resume quality (Mode 2).

Provides standalone resume quality analysis when no job description is given.
"""

from .resume_analyzer import analyze_resume_quality

__all__ = ["analyze_resume_quality"]
