import re
import logging
from app.ml.skill_extractor import skill_extractor

logger = logging.getLogger(__name__)


class CoverLetterService:
    """
    Feature 2: Cover Letter Generator
    Generates tailored cover letters using template + NLP extraction.
    No OpenAI needed — fully local generation with smart templates.
    """

    TONES = ["professional", "enthusiastic", "concise"]

    def generate(
        self,
        resume_text: str,
        jd_text: str,
        applicant_name: str = "Applicant",
        company_name: str = "the company",
        job_title: str = "this position",
        tone: str = "professional",
    ) -> dict:

        if not resume_text or not jd_text:
            return {"error": "Both resume and job description are required"}

        # Extract data from resume
        skills = skill_extractor.extract(resume_text)
        exp_years = skill_extractor.extract_experience_years(resume_text)
        education = skill_extractor.extract_education(resume_text)

        # Extract from JD
        jd_skills = skill_extractor.extract(jd_text)
        matched_skills = list(set(skills) & set(jd_skills))[:5]

        # Extract name from resume if not provided
        if applicant_name == "Applicant":
            applicant_name = self._extract_name(resume_text) or "Applicant"

        # Extract job title from JD if not provided
        if job_title == "this position":
            job_title = self._extract_job_title(jd_text) or "this position"

        # Extract company name from JD if not provided
        if company_name == "the company":
            company_name = self._extract_company(jd_text) or "your company"

        # Generate each paragraph
        opening   = self._opening(applicant_name, job_title, company_name, tone)
        body1     = self._body_skills(matched_skills, skills, exp_years, tone)
        body2     = self._body_value(jd_text, jd_skills, tone)
        closing   = self._closing(company_name, tone)
        signature = f"\nSincerely,\n{applicant_name}"

        letter = f"{opening}\n\n{body1}\n\n{body2}\n\n{closing}{signature}"

        return {
            "cover_letter": letter,
            "applicant_name": applicant_name,
            "job_title": job_title,
            "company_name": company_name,
            "tone": tone,
            "matched_skills_used": matched_skills,
            "word_count": len(letter.split()),
            "paragraphs": {
                "opening": opening,
                "body_skills": body1,
                "body_value": body2,
                "closing": closing,
            },
        }

    # ── Paragraph generators ─────────────────────────────────────

    def _opening(self, name, title, company, tone):
        if tone == "enthusiastic":
            return (
                f"Dear Hiring Manager,\n\n"
                f"I am thrilled to apply for the {title} role at {company}. "
                f"Having followed {company}'s work closely, I am excited by the opportunity "
                f"to contribute my skills and passion to your team."
            )
        elif tone == "concise":
            return (
                f"Dear Hiring Manager,\n\n"
                f"I am applying for the {title} position at {company}. "
                f"I am confident my background aligns well with your requirements."
            )
        else:  # professional
            return (
                f"Dear Hiring Manager,\n\n"
                f"I am writing to express my interest in the {title} position at {company}. "
                f"After reviewing the role requirements, I am confident that my experience "
                f"and skills make me a strong candidate for this opportunity."
            )

    def _body_skills(self, matched_skills, all_skills, exp_years, tone):
        exp_str = f"With {exp_years:.0f} years of experience" if exp_years else "Throughout my career"
        skills_str = (
            ", ".join(matched_skills[:3]) if matched_skills
            else ", ".join(all_skills[:3]) if all_skills
            else "a range of relevant technical and professional skills"
        )

        if tone == "enthusiastic":
            return (
                f"{exp_str}, I have built strong expertise in {skills_str}. "
                f"I love tackling complex challenges and have consistently delivered "
                f"impactful results by applying these skills in fast-paced environments. "
                f"My hands-on experience has prepared me to make an immediate contribution "
                f"to your team."
            )
        elif tone == "concise":
            return (
                f"{exp_str}, I have developed expertise in {skills_str}. "
                f"I have a proven track record of delivering results using these skills."
            )
        else:
            return (
                f"{exp_str}, I have developed strong proficiency in {skills_str}. "
                f"I have successfully applied these skills in professional settings, "
                f"consistently delivering quality work and measurable outcomes. "
                f"My background has equipped me with both the technical knowledge "
                f"and the collaborative mindset needed for this role."
            )

    def _body_value(self, jd_text, jd_skills, tone):
        top_jd_skills = jd_skills[:4] if jd_skills else []
        focus = (
            f"your focus on {', '.join(top_jd_skills[:2])}"
            if top_jd_skills else "your team's goals"
        )

        if tone == "enthusiastic":
            return (
                f"I am particularly drawn to {focus} and believe my experience "
                f"positions me to make an immediate and meaningful impact. "
                f"I thrive in collaborative environments and am always eager to "
                f"learn, grow, and push projects to success."
            )
        elif tone == "concise":
            return (
                f"I am aligned with {focus} and ready to contribute from day one."
            )
        else:
            return (
                f"I am particularly interested in {focus} as outlined in the job description. "
                f"I am confident in my ability to contribute effectively to your team "
                f"and to support the organization's objectives through dedicated, "
                f"high-quality work."
            )

    def _closing(self, company, tone):
        if tone == "enthusiastic":
            return (
                f"I would love the opportunity to discuss how my background can "
                f"contribute to {company}'s continued success. Thank you so much "
                f"for considering my application — I look forward to hearing from you!\n"
            )
        elif tone == "concise":
            return (
                f"I welcome the opportunity to discuss my application further. "
                f"Thank you for your consideration.\n"
            )
        else:
            return (
                f"I would welcome the opportunity to further discuss how my experience "
                f"and skills align with the needs of {company}. Thank you for your time "
                f"and consideration. I look forward to the possibility of contributing "
                f"to your team.\n"
            )

    # ── Extraction helpers ───────────────────────────────────────

    def _extract_name(self, text: str):
        import re
        lines = text.strip().split("\n")
        for line in lines[:5]:
            line = line.strip()
            match = re.match(r"^([A-Z][a-z]+(?:\s[A-Z][a-z]+){1,3})$", line)
            if match and 4 < len(line) < 50:
                return match.group(1)
        return None

    def _extract_job_title(self, jd_text: str):
        import re
        patterns = [
            r"(?:position|role|title|job):\s*([A-Za-z\s]+)",
            r"(?:hiring|seeking|looking for)\s+(?:a|an)?\s*([A-Za-z\s]+(?:developer|engineer|manager|analyst|designer|lead|specialist))",
            r"^([A-Za-z\s]+(?:developer|engineer|manager|analyst|designer|lead|specialist))",
        ]
        for pattern in patterns:
            match = re.search(pattern, jd_text[:500], re.IGNORECASE | re.MULTILINE)
            if match:
                return match.group(1).strip()[:60]
        return None

    def _extract_company(self, jd_text: str):
        import re
        patterns = [
            r"(?:at|join|company|organization|firm):\s*([A-Z][A-Za-z\s&.]+)",
            r"About\s+([A-Z][A-Za-z\s&.]{3,40})",
        ]
        for pattern in patterns:
            match = re.search(pattern, jd_text[:300], re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                if 3 < len(name) < 50:
                    return name
        return None


cover_letter_service = CoverLetterService()