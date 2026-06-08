import re
import logging
import random
from app.ml.skill_extractor import skill_extractor

logger = logging.getLogger(__name__)


class InterviewQuestionsService:
    """
    Feature 3: Interview Question Generator
    Generates role-specific questions with sample answers.
    Fully local — no external API needed.
    """

    # Behavioural questions with sample answer frameworks
    BEHAVIOURAL_QUESTIONS = [
        {
            "question": "Tell me about a time you faced a challenging technical problem. How did you solve it?",
            "category": "Problem Solving",
            "answer_framework": "Use STAR: Describe the Situation and Task. Explain the technical challenge. Walk through your Approach step by step. Share the Result and what you learned.",
            "sample_answer": "In my previous role, our production database was causing slow query times affecting 10,000+ users. I analyzed query execution plans, identified missing indexes, and restructured two core queries. Response time improved by 60% within 24 hours.",
        },
        {
            "question": "Describe a situation where you had to work under pressure to meet a tight deadline.",
            "category": "Time Management",
            "answer_framework": "STAR: Set the scene (deadline, stakes). Your specific role. Steps taken to prioritize and execute. Outcome delivered.",
            "sample_answer": "We had a critical product launch in 48 hours when a key feature broke in staging. I triaged the issue, split tasks with two colleagues, worked in shifts, and we delivered on time with all tests passing.",
        },
        {
            "question": "Give an example of when you had to collaborate with a difficult team member.",
            "category": "Teamwork",
            "answer_framework": "Focus on your actions, not blame. Show empathy, communication skills, and a positive resolution.",
            "sample_answer": "A colleague and I disagreed on architecture choices. I scheduled a 1:1, listened to their concerns, found common ground by prototyping both approaches, and we chose the better-performing solution together.",
        },
        {
            "question": "Tell me about a project you led from start to finish.",
            "category": "Leadership",
            "answer_framework": "Scope → Planning → Execution → Challenges overcome → Results delivered.",
            "sample_answer": "Led a 3-month API redesign with 4 engineers. Created the roadmap, ran weekly standups, unblocked dependencies, and delivered ahead of schedule. API latency dropped 35%.",
        },
        {
            "question": "Describe a time you received critical feedback and how you responded.",
            "category": "Self-Awareness",
            "answer_framework": "Show openness, not defensiveness. What you did with the feedback. How it improved your work.",
            "sample_answer": "My manager flagged that my code reviews were too critical in tone. I took a course on constructive feedback, changed my approach to question-based reviews, and team satisfaction scores improved noticeably.",
        },
    ]

    GENERAL_QUESTIONS = [
        {
            "question": "Why do you want to work at this company?",
            "category": "Motivation",
            "answer_framework": "Research the company beforehand. Connect their mission to your personal goals. Be specific.",
            "sample_answer": "I admire how your company is solving [specific problem]. My background in [skill] aligns with your product roadmap, and I want to contribute to [specific initiative].",
        },
        {
            "question": "Where do you see yourself in 5 years?",
            "category": "Career Goals",
            "answer_framework": "Be honest but align with the role. Show ambition + realism.",
            "sample_answer": "I see myself growing into a senior technical role, possibly leading a team. This position feels like the right next step because [reason specific to role].",
        },
        {
            "question": "What is your greatest professional strength?",
            "category": "Self-Assessment",
            "answer_framework": "Pick ONE strength. Give a specific example. Tie it to the role.",
            "sample_answer": "My strongest skill is breaking down complex problems into clear steps. For example, [specific project] where this approach saved X hours.",
        },
        {
            "question": "What is an area you are actively working to improve?",
            "category": "Growth Mindset",
            "answer_framework": "Be genuine (not fake weaknesses). Show self-awareness + active improvement steps.",
            "sample_answer": "I am working on public speaking. I joined a Toastmasters group 3 months ago and have already presented at 4 internal meetings.",
        },
    ]

    def generate(
        self,
        resume_text: str,
        jd_text: str,
        num_questions: int = 12,
    ) -> dict:

        if not resume_text or not jd_text:
            return {"error": "Both resume and job description are required"}

        # Extract context
        skills = skill_extractor.extract(resume_text)
        jd_skills = skill_extractor.extract(jd_text)
        exp_years = skill_extractor.extract_experience_years(resume_text)
        job_title = self._extract_job_title(jd_text)

        questions = []

        # 1. Technical skill questions (based on JD skills)
        tech_questions = self._generate_technical(jd_skills, skills, job_title)
        questions.extend(tech_questions[:5])

        # 2. Behavioural questions
        selected_behav = random.sample(
            self.BEHAVIOURAL_QUESTIONS,
            min(4, len(self.BEHAVIOURAL_QUESTIONS))
        )
        questions.extend([{**q, "category": "Behavioural — " + q["category"]} for q in selected_behav])

        # 3. General questions
        selected_general = random.sample(
            self.GENERAL_QUESTIONS,
            min(3, len(self.GENERAL_QUESTIONS))
        )
        questions.extend(selected_general)

        # 4. Experience-level question
        if exp_years is not None:
            questions.append(self._experience_question(exp_years, job_title))

        # Number them and trim
        questions = questions[:num_questions]
        for i, q in enumerate(questions, start=1):
            q["number"] = i

        return {
            "questions": questions,
            "total": len(questions),
            "job_title": job_title,
            "detected_skills": skills[:10],
            "jd_required_skills": jd_skills[:10],
            "experience_years": exp_years,
            "preparation_tips": self._preparation_tips(jd_skills),
        }

    def _generate_technical(self, jd_skills, resume_skills, job_title):
        """Generate skill-specific technical questions."""
        questions = []
        matched = list(set(jd_skills) & set(resume_skills))
        missing = list(set(jd_skills) - set(resume_skills))

        # Questions on matched skills (you know them — go deep)
        for skill in matched[:3]:
            q = self._tech_question_for_skill(skill, depth="deep")
            if q:
                questions.append(q)

        # Questions on missing skills (basic intro questions)
        for skill in missing[:2]:
            q = self._tech_question_for_skill(skill, depth="basic")
            if q:
                questions.append(q)

        return questions

    def _tech_question_for_skill(self, skill: str, depth: str) -> dict:
        templates_deep = [
            {
                "question": f"Describe a complex project where you used {skill}. What challenges did you face?",
                "category": f"Technical — {skill.title()}",
                "answer_framework": f"Project scope → How you applied {skill} → Specific challenges → Solutions → Outcomes.",
                "sample_answer": f"Walk the interviewer through a specific project, highlighting your depth of {skill} knowledge and problem-solving approach.",
            },
            {
                "question": f"What are the best practices you follow when working with {skill}?",
                "category": f"Technical — {skill.title()}",
                "answer_framework": "List 3–4 concrete practices. Give a real example for at least one.",
                "sample_answer": f"For {skill}, I always prioritize [practice 1], [practice 2], and [practice 3]. In [project], applying [practice] led to [outcome].",
            },
        ]

        templates_basic = [
            {
                "question": f"The job requires {skill}. What is your current experience level with it?",
                "category": f"Technical — {skill.title()}",
                "answer_framework": "Be honest. Show learning mindset. Mention related skills. Share how you plan to bridge the gap.",
                "sample_answer": f"I have foundational exposure to {skill} through [project/course]. I am actively upskilling and have [specific action] underway.",
            },
        ]

        templates = templates_deep if depth == "deep" else templates_basic
        return random.choice(templates) if templates else None

    def _experience_question(self, exp_years: float, job_title: str) -> dict:
        if exp_years < 2:
            return {
                "number": 0,
                "question": "You are early in your career. How do you plan to get up to speed quickly?",
                "category": "Experience",
                "answer_framework": "Show proactivity: online courses, side projects, mentors, reading docs.",
                "sample_answer": "I offset limited years with fast learning. I have [self-study examples] and [project]. I ask good questions and document everything I learn.",
            }
        else:
            return {
                "number": 0,
                "question": f"With {exp_years:.0f} years of experience, what has been your most impactful project?",
                "category": "Experience",
                "answer_framework": "STAR. Emphasize scale, ownership, and measurable impact.",
                "sample_answer": f"My most impactful project was [describe it]. I owned [specific part], overcame [challenge], and the result was [measurable outcome].",
            }

    def _extract_job_title(self, jd_text: str) -> str:
        patterns = [
            r"(?:hiring|seeking|looking for)\s+(?:a|an)?\s*([A-Za-z\s]+(?:developer|engineer|manager|analyst|designer|lead|specialist))",
            r"^([A-Za-z\s]+(?:developer|engineer|manager|analyst|designer|lead|specialist))",
            r"(?:position|role|title):\s*([^\n]+)",
        ]
        for pattern in patterns:
            m = re.search(pattern, jd_text[:500], re.IGNORECASE | re.MULTILINE)
            if m:
                return m.group(1).strip()[:60]
        return "the role"

    def _preparation_tips(self, jd_skills: list) -> list:
        tips = [
            "Research the company's products, mission, and recent news before the interview.",
            "Prepare 3–5 STAR stories that demonstrate your key skills.",
            "Have questions ready to ask the interviewer about the team and role.",
            "Practice out loud — timing yourself for 2-minute answers.",
        ]
        if jd_skills:
            tips.append(
                f"Review fundamentals of: {', '.join(jd_skills[:4])} — "
                "common interview topics for this role."
            )
        return tips


interview_questions_service = InterviewQuestionsService()