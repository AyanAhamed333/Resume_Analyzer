import re
from collections import Counter

ROLES = {
    "backend": {
        "skills": ["python", "flask", "sql", "api"],
        "weights": {"python": 2, "flask": 2, "sql": 1, "api": 1}
    },
    "data": {
        "skills": ["python", "pandas", "sql", "excel"],
        "weights": {"python": 2, "pandas": 2, "sql": 1, "excel": 1}
    },
    "marketing": {
        "skills": ["seo", "content", "campaign", "social media", "analytics"],
        "weights": {"seo": 2, "campaign": 2, "content": 1, "social media": 1, "analytics": 1}
    },
    "sales": {
        "skills": ["crm", "negotiation", "b2b", "lead generation", "communication"],
        "weights": {"negotiation": 2, "b2b": 2, "crm": 1, "lead generation": 1, "communication": 1}
    },
    "hr": {
        "skills": ["recruitment", "onboarding", "payroll", "employee relations", "interviews"],
        "weights": {"recruitment": 2, "employee relations": 2, "onboarding": 1, "payroll": 1, "interviews": 1}
    },
    "teacher": {
        "skills": ["lesson planning", "curriculum", "classroom management", "communication", "grading"],
        "weights": {"lesson planning": 2, "classroom management": 2, "curriculum": 1, "communication": 1, "grading": 1}
    }
}

STOP_WORDS = set([
    "the", "and", "to", "of", "a", "in", "for", "is", "with", "on", "as", "that", "this", "or", "by", "from", 
    "an", "at", "be", "we", "are", "will", "you", "your", "our", "their", "have", "has", "not", "it", "can",
    "such", "which", "more", "about", "other", "all", "work", "team", "experience", "skills", "required", 
    "requirements", "years", "working", "knowledge", "ability", "strong", "including", "development", 
    "business", "support", "management", "ensure", "provide", "using", "looking", "good", "understanding", 
    "framework", "plus", "familiarity", "building", "excellent", "written", "verbal", "communication", 
    "environment", "related", "field", "degree", "equivalent", "preferred", "must", "some", "any", "well", 
    "also", "new", "used", "make", "take", "get", "way", "day", "may", "part", "time", "full", "job", "role", 
    "company", "join", "help", "candidate", "ideal", "seeking", "seek", "responsibilities", "include", 
    "require", "opportunity", "benefits", "salary", "pay", "remote", "location", "office", "based", "design", 
    "develop", "maintain", "test", "deploy", "implement", "build", "collaborate", "participate", "contribute", 
    "manage", "lead", "troubleshoot", "resolve", "issues", "quality", "performance", "best", "practices", 
    "user", "users", "customer", "customers", "client", "clients", "within", "through", "into", "highly", "key"
])

ACTION_VERBS = ["managed", "developed", "led", "created", "designed", "improved", "increased", "reduced", "delivered"]

def extract_jd_keywords(jd_text, top_n=10):
    words = re.findall(r'\b[a-z]{3,}\b', jd_text.lower())
    filtered_words = [w for w in words if w not in STOP_WORDS]
    word_counts = Counter(filtered_words)
    return [word for word, count in word_counts.most_common(top_n)]

def analyze_resume(text, role_key, jd_text=""):
    if not text:
        return None

    role_key = role_key.lower() if role_key else ""
    text_lower = text.lower()
    
    required_skills = []
    weights = {}
    
    # Determine target skills (either from JD or predefined role)
    if jd_text:
        jd_keywords = extract_jd_keywords(jd_text, top_n=12)
        required_skills = jd_keywords
        weights = {kw: 1 for kw in jd_keywords}  # Equal weight for auto-extracted JD words
    elif role_key in ROLES:
        role_data = ROLES[role_key]
        required_skills = role_data["skills"]
        weights = role_data["weights"]
    else:
        return None  # Neither JD nor valid role provided

    skills_found = []
    missing_skills = []
    
    total_weight = sum(weights.values())
    earned_weight = 0
    
    # Match skills
    for skill in required_skills:
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, text_lower):
            skills_found.append(skill)
            earned_weight += weights.get(skill, 1)
        else:
            missing_skills.append(skill)

    # Base score
    score = int((earned_weight / total_weight) * 100) if total_weight > 0 else 0
    
    # Enhanced Suggestions Engine
    suggestions = []
    
    # 1. Missing skills suggestions
    for missing in missing_skills[:2]:
        suggestions.append(f"Consider adding '{missing}' to your resume to better match the requirements.")
    
    # 2. Length check
    word_count = len(re.findall(r'\b\w+\b', text))
    if word_count < 150:
        suggestions.append(f"Your resume seems a bit short ({word_count} words). Try detailing your responsibilities more.")
    elif word_count > 800:
        suggestions.append(f"Your resume is quite long ({word_count} words). Consider trimming to keep it concise.")

    # 3. Action verbs check
    found_action_verbs = [v for v in ACTION_VERBS if re.search(r'\b' + v + r'\b', text_lower)]
    if not found_action_verbs:
        suggestions.append("We didn't detect strong action verbs (e.g., 'managed', 'developed'). Start your bullet points with them!")
        
    # 4. Metrics check
    has_metrics = re.search(r'\d+%|\$\d+|\b\d+\s*(million|billion|k|m)\b', text_lower)
    if not has_metrics:
        suggestions.append("Try to quantify your achievements using numbers, percentages, or dollar amounts.")

    # 5. General score tip
    if score < 50 and len(suggestions) < 5:
        suggestions.append("Review the missing skills and try to add relevant projects to boost your match score.")
    elif score >= 80 and len(suggestions) < 5:
        suggestions.append("Great job! Your resume aligns very well with the requirements.")

    return {
        "score": score,
        "skills_found": skills_found,
        "missing_skills": missing_skills,
        "suggestions": suggestions[:5]  # Return up to 5 tips now
    }
