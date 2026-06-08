import re
import logging
from typing import List

logger = logging.getLogger(__name__)

STANDARD_FONTS_NOTE = "Use standard fonts: Arial, Calibri, Times New Roman, Helvetica."

PREFERRED_SECTIONS_ORDER = [
    "contact", "summary", "objective", "experience",
    "education", "skills", "projects", "certifications",
]

ATS_UNFRIENDLY_PATTERNS = [
    (r"<table", "Tables can confuse ATS parsers — use plain text instead"),
    (r"header|footer", "Content in headers/footers is often missed by ATS"),
    (r"\|{2,}", "Pipe characters used as dividers may cause parsing errors"),
]


class ATSCheckerService:
    """
    Feature 6: ATS Checker
    Scores resume compatibility with Applicant Tracking Systems.
    """

    def check(self, resume_text: str, file_extension: str = ".pdf") -> dict:
        if not resume_text:
            return {"error": "No resume text provided"}

        checks = {}
        suggestions = []
        total_score = 0
        max_score = 100

        # 1. File format check (15 pts)
        fmt_score, fmt_issues = self._check_format(file_extension)
        checks["file_format"] = {"score": fmt_score, "max": 15, "issues": fmt_issues}
        total_score += fmt_score
        suggestions.extend(fmt_issues)

        # 2. Section order check (20 pts)
        sec_score, sec_issues = self._check_sections(resume_text)
        checks["section_structure"] = {"score": sec_score, "max": 20, "issues": sec_issues}
        total_score += sec_score
        suggestions.extend(sec_issues)

        # 3. Keyword density (20 pts)
        kw_score, kw_issues, kw_details = self._check_keywords(resume_text)
        checks["keyword_density"] = {
            "score": kw_score, "max": 20,
            "issues": kw_issues, "details": kw_details,
        }
        total_score += kw_score
        suggestions.extend(kw_issues)

        # 4. Contact info check (20 pts)
        ct_score, ct_issues = self._check_contact(resume_text)
        checks["contact_info"] = {"score": ct_score, "max": 20, "issues": ct_issues}
        total_score += ct_score
        suggestions.extend(ct_issues)

        # 5. Readability check (15 pts)
        rd_score, rd_issues = self._check_readability(resume_text)
        checks["readability"] = {"score": rd_score, "max": 15, "issues": rd_issues}
        total_score += rd_score
        suggestions.extend(rd_issues)

        # 6. Length check (10 pts)
        ln_score, ln_issues = self._check_length(resume_text)
        checks["length"] = {"score": ln_score, "max": 10, "issues": ln_issues}
        total_score += ln_score
        suggestions.extend(ln_issues)

        total_score = min(total_score, 100)

        return {
            "ats_score": total_score,
            "grade": self._grade(total_score),
            "checks": checks,
            "suggestions": suggestions,
            "font_warning": STANDARD_FONTS_NOTE,
            "summary": self._summary(total_score),
        }

    def _check_format(self, ext: str):
        if ext in (".pdf", ".docx"):
            return 15, []
        elif ext in (".doc", ".txt"):
            return 10, ["Prefer PDF or DOCX for best ATS compatibility"]
        else:
            return 0, [f"Format '{ext}' is not ATS-friendly. Convert to PDF or DOCX"]

    def _check_sections(self, text: str):
        text_lower = text.lower()
        found_sections = []
        missing_sections = []

        section_keywords = {
            "contact":        ["contact", "email", "phone", "address"],
            "summary":        ["summary", "objective", "profile", "about me"],
            "experience":     ["experience", "employment", "work history", "career"],
            "education":      ["education", "academic", "qualification", "degree"],
            "skills":         ["skills", "technical skills", "competencies", "expertise"],
            "projects":       ["projects", "portfolio", "work samples"],
            "certifications": ["certification", "certificate", "award", "achievement"],
        }

        for section, keywords in section_keywords.items():
            if any(kw in text_lower for kw in keywords):
                found_sections.append(section)
            elif section in ["contact", "experience", "education", "skills"]:
                missing_sections.append(section)

        issues = []
        if missing_sections:
            issues.append(
                f"Missing critical sections: {', '.join(missing_sections)}. "
                "ATS systems look for these headings specifically."
            )

        score = max(0, 20 - len(missing_sections) * 5)
        return score, issues

    def _check_keywords(self, text: str):
        text_lower = text.lower()

        action_verbs = [
            "managed", "developed", "led", "created", "implemented",
            "designed", "built", "achieved", "improved", "increased",
            "reduced", "delivered", "coordinated", "analyzed", "launched",
        ]

        quantifiers = re.findall(
            r"\b\d+\s*(%|percent|million|thousand|k\b|users|customers|projects|teams?)\b",
            text_lower
        )

        found_verbs = [v for v in action_verbs if v in text_lower]
        verb_count = len(found_verbs)
        quant_count = len(quantifiers)

        issues = []
        if verb_count < 5:
            issues.append(
                f"Only {verb_count} action verbs found. Use strong verbs like: "
                "managed, developed, led, implemented, achieved."
            )
        if quant_count < 2:
            issues.append(
                "Add quantified achievements (e.g., 'Increased sales by 30%', "
                "'Managed team of 10') to stand out."
            )

        score = min(20, verb_count * 2 + quant_count * 3)
        return score, issues, {
            "action_verbs_found": found_verbs[:5],
            "quantified_achievements": quant_count,
        }

    def _check_contact(self, text: str):
        issues = []
        score = 20

        if not re.search(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b", text):
            issues.append("No email address found. Add your professional email.")
            score -= 8

        if not re.search(r"(\+?\d[\d\s\-().]{7,}\d)", text):
            issues.append("No phone number detected. Add your contact number.")
            score -= 6

        if not re.search(r"\b[A-Z][a-z]+\s+[A-Z][a-z]+\b", text[:500]):
            issues.append("Name not clearly detected in first section. Put your name at the top.")
            score -= 6

        return max(0, score), issues

    def _check_readability(self, text: str):
        issues = []
        score = 15

        # Check for very long lines (possible parsing issue)
        lines = text.split("\n")
        long_lines = [l for l in lines if len(l) > 200]
        if len(long_lines) > 5:
            issues.append(
                "Several very long lines detected. Break content into bullet points "
                "for better ATS parsing."
            )
            score -= 5

        # Check for special characters
        special = re.findall(r"[^\x00-\x7F]", text)
        if len(special) > 10:
            issues.append(
                f"{len(special)} non-ASCII characters found. "
                "Remove special symbols — they may cause ATS parsing errors."
            )
            score -= 5

        # Check for tables (pipe-based)
        if text.count("|") > 10:
            issues.append("Possible table detected. ATS systems often fail to parse tables.")
            score -= 5

        return max(0, score), issues

    def _check_length(self, text: str):
        words = len(text.split())
        issues = []

        if words < 200:
            issues.append(f"Resume too short ({words} words). Aim for 400–800 words.")
            return 2, issues
        elif words < 400:
            issues.append(f"Resume may be too brief ({words} words). Add more detail.")
            return 6, issues
        elif words > 1200:
            issues.append(
                f"Resume very long ({words} words). Consider trimming to 1–2 pages "
                "for better ATS and recruiter readability."
            )
            return 7, issues
        else:
            return 10, []

    def _grade(self, score: int) -> str:
        if score >= 85:
            return "A — Excellent ATS compatibility"
        elif score >= 70:
            return "B — Good ATS compatibility"
        elif score >= 55:
            return "C — Moderate — improvements needed"
        elif score >= 40:
            return "D — Poor — major fixes required"
        else:
            return "F — Very poor ATS compatibility"

    def _summary(self, score: int) -> str:
        if score >= 85:
            return "Your resume is highly ATS-compatible. Focus on tailoring content per job."
        elif score >= 70:
            return "Good ATS score. Address the suggestions above to maximize visibility."
        elif score >= 55:
            return "Moderate ATS compatibility. Several improvements needed before applying."
        else:
            return "Low ATS score. Your resume may be filtered out. Fix the issues above first."


ats_checker_service = ATSCheckerService()