import logging
from app.ml.similarity import similarity_engine
from app.ml.skill_extractor import skill_extractor

logger = logging.getLogger(__name__)


class ResumeEnhancerService:
    """
    Feature 1: Resume Enhancer
    Computes selection probability and interview eligibility
    by comparing resume against job description.
    """

    def analyze(self, resume_text: str, jd_text: str) -> dict:
        if not resume_text or not jd_text:
            return {"error": "Both resume and job description text are required"}

        # Core match computation
        match = similarity_engine.compute_match(resume_text, jd_text)

        # Experience analysis
        exp_years = skill_extractor.extract_experience_years(resume_text)
        education = skill_extractor.extract_education(resume_text)

        # Build improvement suggestions
        suggestions = self._build_suggestions(match, exp_years)

        # Section scores
        section_scores = self._score_sections(resume_text)

        return {
            "overall_score": match["score"],
            "selection_probability": match["selection_probability"],
            "interview_eligible": match["interview_eligible"],
            "eligibility_label": match["eligibility_label"],
            "embedding_score": match["embedding_score"],
            "skill_overlap_score": match["skill_overlap_score"],
            "matched_skills": match["matched_skills"],
            "missing_skills": match["missing_skills"],
            "resume_skills": match["resume_skills"],
            "jd_required_skills": match["jd_skills"],
            "experience_years_detected": exp_years,
            "education_detected": education,
            "section_scores": section_scores,
            "improvement_suggestions": suggestions,
            "summary": self._build_summary(match, exp_years),
        }

    def _score_sections(self, text: str) -> dict:
        """Score individual resume sections."""
        import re
        text_lower = text.lower()

        def has_section(keywords):
            return any(re.search(r"\b" + kw + r"\b", text_lower) for kw in keywords)

        def section_score(keywords, content_check=None):
            present = has_section(keywords)
            if not present:
                return 0
            if content_check:
                return 10 if content_check(text_lower) else 5
            return 10

        contact_score = 10 if re.search(
            r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b", text
        ) else 0

        skills_count = len(skill_extractor.extract(text))
        skills_score = min(10, skills_count * 2)

        return {
            "contact_info": contact_score,
            "summary_objective": section_score(["summary", "objective", "profile", "about"]),
            "work_experience": section_score(["experience", "employment", "work history"]),
            "education": section_score(["education", "university", "degree", "college"]),
            "skills": skills_score,
            "projects": section_score(["projects", "portfolio", "github"]),
            "certifications": section_score(["certification", "certified", "licence", "award"]),
        }

    def _build_suggestions(self, match: dict, exp_years) -> list:
        suggestions = []

        if match["score"] < 65:
            suggestions.append(
                "Your overall match score is below the interview threshold (65%). "
                "Focus on adding the missing skills listed below."
            )

        missing = match.get("missing_skills", [])
        if missing:
            top_missing = missing[:5]
            suggestions.append(
                f"Add these missing skills to your resume: {', '.join(top_missing)}. "
                "Use them naturally in your experience bullet points."
            )

        if match["embedding_score"] < 50:
            suggestions.append(
                "Your resume language does not closely match the job description. "
                "Try mirroring keywords and phrases from the job posting."
            )

        if match["skill_overlap_score"] < 40:
            suggestions.append(
                "Low skill overlap detected. Review the job requirements carefully "
                "and explicitly list all relevant skills you have."
            )

        if exp_years and exp_years < 1:
            suggestions.append(
                "Limited experience detected. Add internships, freelance work, "
                "or personal projects to strengthen your profile."
            )

        if not suggestions:
            suggestions.append(
                "Strong match! Tailor your cover letter to highlight your "
                f"top matching skills: {', '.join(match['matched_skills'][:3])}."
            )

        return suggestions

    def _build_summary(self, match: dict, exp_years) -> str:
        score = match["score"]
        eligible = match["interview_eligible"]
        matched = len(match["matched_skills"])
        missing = len(match["missing_skills"])
        exp_str = f"{exp_years} years experience" if exp_years else "experience not detected"

        if eligible:
            return (
                f"Strong candidate — {score:.0f}% match. "
                f"{matched} skills matched, {missing} missing. {exp_str}. "
                f"You are interview eligible for this role."
            )
        else:
            return (
                f"Below threshold — {score:.0f}% match. "
                f"{matched} skills matched, {missing} missing. {exp_str}. "
                f"Add missing skills to improve your chances."
            )


resume_enhancer_service = ResumeEnhancerService()