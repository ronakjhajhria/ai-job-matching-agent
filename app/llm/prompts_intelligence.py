def parse_resume_messages(resume_text: str) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": "You are a precise resume parser. Extract the requested fields based ONLY on the provided resume."
        },
        {
            "role": "user",
            "content": f"Parse this resume:\n\n{resume_text}"
        }
    ]

def parse_job_messages(jd_text: str) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": "You are a precise job description parser. Extract the requested fields based ONLY on the provided job posting."
        },
        {
            "role": "user",
            "content": f"Parse this job description:\n\n{jd_text}"
        }
    ]

def match_job_messages(resume_profile: str, job_profile: str) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "You are an expert career coach. Compare the candidate's resume profile against the job description profile. "
                "Identify matching skills, missing skills, and provide a holistic score and explanation based on evidence."
            )
        },
        {
            "role": "user",
            "content": f"RESUME PROFILE:\n{resume_profile}\n\nJOB PROFILE:\n{job_profile}"
        }
    ]
