from django.core.management.base import BaseCommand
from blog.models import BlogPost

POSTS = [
    dict(
        title="How to Prepare for Loksewa Exam 2025: Complete Guide",
        category="loksewa_update",
        author_name="NepHub Team",
        is_featured=True,
        excerpt="Preparing for the Public Service Commission exam requires a structured approach. Here is everything you need to know to succeed in 2025.",
        content="""The Lok Sewa Aayog (Public Service Commission) exam is one of the most competitive examinations in Nepal. Every year, thousands of candidates compete for a limited number of government positions.

Getting Started
The first step is to visit the official PSC website at psc.gov.np and register for the vacancy notification alerts. Make sure your citizenship and educational documents are ready.

Study Strategy
1. Understand the syllabus: Each post has a specific syllabus. Download it from psc.gov.np.
2. Current affairs: Read a Nepali newspaper daily. Questions on current events are common.
3. General knowledge: Focus on Nepal's constitution, history, geography, and governance.
4. Mathematics and reasoning: Practice arithmetic and logical reasoning daily.

Time Management
Allocate at least 4 hours per day for study. Divide your time across all subjects evenly. Solve past question papers from the last 5 years — patterns repeat frequently.

Physical Preparation
Some posts require a physical fitness test. Start jogging and basic exercises 3 months before the exam if this applies to your post.

Final Tips
Apply at least 5 days before the deadline. Bring original documents on exam day. Check the PSC website for any updates or changes to the schedule.

Best of luck from the NepHub team!"""
    ),
    dict(
        title="Top 10 Scholarships for Nepali Students in 2025",
        category="scholarship_news",
        author_name="NepHub Team",
        is_featured=False,
        excerpt="From Japan's MEXT to the Fulbright Program — here are the top fully funded scholarships available to Nepali students this year.",
        content="""Nepal has excellent access to international scholarship programs. Here are the top opportunities for 2025.

1. Japanese Government (MEXT) Scholarship
Fully funded scholarship for undergraduate and graduate study in Japan. Covers tuition, accommodation, and a monthly stipend. Apply through the Embassy of Japan in Kathmandu.

2. Fulbright Program (USA)
For graduate study and research in the United States. Covers tuition, living expenses, and travel. Highly competitive — start preparing your Statement of Purpose early.

3. Chevening Scholarship (UK)
Fully funded one-year master's degree in the UK. Open to Nepali professionals with 2+ years of work experience.

4. Erasmus Mundus (Europe)
Joint master's degrees across European universities. Excellent stipend and travel allowance included.

5. Commonwealth Scholarship (UK/Canada/Australia)
Available for master's and PhD programs. Strong preference for candidates who will return to contribute to Nepal's development.

6. Korean Government Scholarship (KGSP)
Undergraduate and graduate programs in South Korea. Includes Korean language training.

7. Chinese Government Scholarship
Wide range of programs at top Chinese universities. Apply through the Chinese Embassy in Kathmandu.

8. Australian Awards Scholarship
For graduate study in Australia. Strong focus on development-relevant fields.

9. TU PhD Scholarship
Tribhuvan University offers domestic scholarships for MPhil and PhD programs for Nepali citizens.

10. Aga Khan Foundation Scholarship
Need-based international scholarships for Nepali students with strong academic records.

Pro Tips
Prepare your IELTS or TOEFL at least 6 months before deadlines. Your Statement of Purpose is the most critical document — get it reviewed by seniors who have received similar scholarships."""
    ),
    dict(
        title="Working in Qatar: Rights, Salaries, and What to Expect",
        category="foreign_news",
        author_name="NepHub Team",
        is_featured=False,
        excerpt="Thousands of Nepalis work in Qatar every year. Here is a clear, honest guide on salaries, working conditions, legal rights, and how to stay safe.",
        content="""Qatar is one of the top destinations for Nepali migrant workers. With proper knowledge and preparation, it can be a life-changing opportunity.

Average Salaries
Construction workers: QAR 1,200 — 1,800/month
Housekeeping/hospitality: QAR 1,000 — 1,500/month
Security guards: QAR 1,200 — 1,600/month
Drivers: QAR 1,400 — 2,000/month
Skilled tradespeople: QAR 2,000 — 3,500/month

Your Legal Rights
Since Qatar's labour reforms, workers have several important rights:
- Right to change employers without needing NOC (under certain conditions)
- Minimum wage: QAR 1,000/month
- Free accommodation and meals must be provided for many categories
- One day off per week
- 30 days paid annual leave after one year

How to Stay Safe
1. Only use DOFE-licensed manpower companies. Verify at dofe.gov.np before paying any fees.
2. Never pay more than the official service charge limit set by DOFE.
3. Keep copies of your passport, contract, and all documents in a secure location.
4. Save the Nepal Embassy contact in Doha: +974-4467-1995

Before You Leave
- Attend the pre-departure orientation at DOFE.
- Make sure your contract specifies salary, job title, and working hours.
- Open a bank account before departure to receive remittances safely.

The NepHub team wishes all Nepali workers abroad safety, health, and prosperity."""
    ),
    dict(
        title="5 CV Mistakes That Cost Nepali Job Seekers Interviews",
        category="tips",
        author_name="NepHub Team",
        is_featured=False,
        excerpt="A weak CV is the number one reason qualified candidates get rejected before the interview. Avoid these five common mistakes that Nepali job seekers make.",
        content="""Your CV is your first impression. Here are five critical mistakes to avoid.

Mistake 1: Generic Objective Statement
"Seeking a challenging position to utilise my skills" tells employers nothing. Replace it with a specific summary: "Civil Engineer with 3 years of road construction experience in Province 1, seeking a project management role."

Mistake 2: Missing or Wrong Contact Information
Always include a working phone number, professional email address, and your location (district/city). Many candidates list email addresses they never check.

Mistake 3: No Quantified Achievements
"Responsible for sales" is weak. "Increased branch sales by 35% in 6 months through daily field visits" is powerful. Add numbers wherever possible.

Mistake 4: Spelling and Grammar Errors
In Nepal, many CVs are submitted with basic English errors. Have at least two people proofread your CV before sending. Use spell-check tools.

Mistake 5: Sending the Same CV for Every Job
Tailor your CV for each application. Highlight the skills and experiences most relevant to each specific job description. This takes 10 extra minutes but dramatically improves your chances.

Bonus Tip
Keep your CV to 1-2 pages maximum. Recruiters in Nepal spend an average of 30 seconds on an initial CV review. Make every line count.

Upload your CV to NepHub for free — keep it updated and accessible anytime you find a job you want to apply for."""
    ),
    dict(
        title="Private Sector Job Market in Nepal: 2025 Outlook",
        category="news",
        author_name="NepHub Team",
        is_featured=False,
        excerpt="Nepal's private sector is showing strong recovery. IT, banking, hospitality, and NGO sectors are hiring actively. Here's what job seekers need to know.",
        content="""Nepal's private sector job market is showing positive momentum in 2025. Several industries are actively hiring and offer competitive salaries.

IT and Technology
The IT sector continues to grow rapidly. Companies like Cloudfactory, Deerwalk, Cotiviti Nepal, and F1Soft are hiring software developers, data analysts, and QA engineers. Average salary for junior developers: NPR 40,000 — 80,000/month.

Banking and Finance
Commercial banks, development banks, and microfinance institutions are Nepal's most consistent employers. BFIs typically hire through their own portals and sometimes through NepHub. Key roles: tellers, loan officers, branch managers.

Hospitality and Tourism
Post-pandemic recovery has been strong. Hotels, trekking companies, and travel agencies are hiring guides, hospitality staff, and marketing professionals.

NGO and INGO Sector
International NGOs including UN agencies, USAID-funded programs, and large INGOs are actively recruiting. Roles in project coordination, M&E, and field work pay well.

How to Succeed in Private Sector Job Hunting
1. Polish your LinkedIn profile — recruiters actively search there.
2. Apply within 48 hours of a job posting — early applicants get more attention.
3. Prepare for competency-based interview questions.
4. Follow up politely one week after applying if you haven't heard back.

Browse all current private sector openings on NepHub — updated daily."""
    ),
]


class Command(BaseCommand):
    help = 'Seed sample blog posts'

    def handle(self, *args, **kwargs):
        count = 0
        for data in POSTS:
            post, created = BlogPost.objects.get_or_create(
                title=data['title'],
                defaults=data
            )
            if created:
                count += 1
        self.stdout.write(self.style.SUCCESS(f'Created {count} blog posts.'))
