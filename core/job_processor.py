"""Job processing pipeline - integrates all parsers."""
from datetime import datetime
from typing import Optional

from data.models.job import JobPosting
from parsers.salary import SalaryParser
from parsers.experience import ExperienceParser
from parsers.sentiment import SentimentAnalyzer
from parsers.nlp import NLPExtractor
from utils.logger import logger


class JobProcessor:
    """Process and enrich job postings with parsed data."""

    def __init__(self):
        """Initialize job processor with all parsers."""
        self.salary_parser = SalaryParser()
        self.experience_parser = ExperienceParser()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.nlp_extractor = NLPExtractor()

    def process(self, job: JobPosting) -> JobPosting:
        """Process job posting through all parsers.

        Args:
            job: Raw JobPosting

        Returns:
            Enriched JobPosting with parsed data
        """
        # Combine title and description for analysis
        full_text = f"{job.title}\n{job.description or ''}"

        try:
            # Parse salary
            salary_info = self.salary_parser.parse(full_text)
            if salary_info:
                job.salary_min = salary_info.min
                job.salary_max = salary_info.max
                job.salary_currency = salary_info.currency
                job.salary_period = salary_info.period
                logger.debug(f"Detected salary: {self.salary_parser.format_salary(salary_info)}")

            # Parse experience level
            experience_levels = self.experience_parser.parse(full_text)
            if experience_levels:
                job.experience_level = ", ".join(experience_levels)
                logger.debug(f"Detected experience level: {job.experience_level}")

            # Analyze sentiment and red flags
            sentiment = self.sentiment_analyzer.analyze(full_text)
            job.sentiment_score = sentiment["score"]
            job.red_flags = sentiment["red_flags"]
            if sentiment["is_suspicious"]:
                logger.warning(f"Suspicious job detected: {job.url}")

            # Extract location and remote status
            location_info = self.nlp_extractor.extract_location(full_text)
            job.location = location_info["location"]
            job.is_remote = location_info["is_remote"]

            # Extract skills
            skills = self.nlp_extractor.extract_skills(full_text)
            job.matched_keywords = skills[:20]  # Limit to top 20 skills

            # Extract company name if not already set
            if not job.company_name:
                company = self.nlp_extractor.extract_company_name(full_text)
                if company:
                    job.company_name = company

            logger.info(
                f"Processed job: {job.title} | "
                f"Salary: {'Yes' if job.salary_min else 'No'} | "
                f"Level: {job.experience_level or 'Unknown'} | "
                f"Skills: {len(job.matched_keywords)}"
            )

        except Exception as e:
            logger.error(f"Error processing job {job.url}: {e}")

        return job

    def process_batch(self, jobs: list) -> list:
        """Process multiple jobs.

        Args:
            jobs: List of JobPosting instances

        Returns:
            List of processed JobPosting instances
        """
        processed = []

        for job in jobs:
            try:
                processed_job = self.process(job)
                processed.append(processed_job)
            except Exception as e:
                logger.error(f"Failed to process job {job.url}: {e}")
                # Still include the job, just unprocessed
                processed.append(job)

        return processed

    def get_processing_stats(self, jobs: list) -> dict:
        """Get statistics about processed jobs.

        Args:
            jobs: List of processed JobPosting instances

        Returns:
            Dictionary with statistics
        """
        stats = {
            "total": len(jobs),
            "with_salary": sum(1 for j in jobs if j.salary_min),
            "with_experience": sum(1 for j in jobs if j.experience_level),
            "remote": sum(1 for j in jobs if j.is_remote),
            "with_red_flags": sum(1 for j in jobs if j.red_flags),
            "avg_skills_per_job": sum(len(j.matched_keywords) for j in jobs) / len(jobs) if jobs else 0
        }

        return stats


# Global processor instance
_processor: Optional[JobProcessor] = None


def get_job_processor() -> JobProcessor:
    """Get global job processor instance.

    Returns:
        JobProcessor instance
    """
    global _processor
    if _processor is None:
        _processor = JobProcessor()
    return _processor
