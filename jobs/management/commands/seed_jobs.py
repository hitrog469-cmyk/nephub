from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
from jobs.models import Job


SAMPLE_JOBS = [
    # Government
    dict(title="Assistant Computer Officer", organization="Ministry of Finance, Nepal",
         category="government", deadline=date.today()+timedelta(days=12),
         apply_link="https://mofe.gov.np", source="mofe.gov.np",
         description="The Ministry of Finance is seeking qualified candidates for the position of Assistant Computer Officer. Candidates must have a bachelor's degree in Computer Science or related field."),
    dict(title="Junior Engineer (Civil)", organization="Department of Roads",
         category="government", deadline=date.today()+timedelta(days=5),
         apply_link="https://dor.gov.np", source="dor.gov.np",
         description="Open position for Junior Engineer in Civil Engineering department. B.E. in Civil Engineering required."),
    dict(title="Section Officer", organization="Office of the Prime Minister",
         category="government", deadline=date.today()+timedelta(days=20),
         apply_link="https://opmcm.gov.np", source="opmcm.gov.np",
         description="Section Officer vacancy at the Office of the Prime Minister and Council of Ministers."),
    dict(title="Accountant", organization="Ministry of Agriculture",
         category="government", deadline=date.today()+timedelta(days=2),
         apply_link="https://moald.gov.np", source="moald.gov.np",
         description="Accountant position with experience in government financial management systems."),

    # Loksewa
    dict(title="Kharidar (Non-Technical)", organization="Lok Sewa Aayog",
         category="loksewa", deadline=date.today()+timedelta(days=18),
         apply_link="https://psc.gov.np", source="psc.gov.np",
         description="Public Service Commission Nepal is accepting applications for Kharidar (Non-Technical) positions across various ministries and departments."),
    dict(title="Nayab Subba", organization="Lok Sewa Aayog",
         category="loksewa", deadline=date.today()+timedelta(days=25),
         apply_link="https://psc.gov.np", source="psc.gov.np",
         description="Nayab Subba vacancies open for written examination. Minimum qualifications: 10+2 or equivalent."),
    dict(title="Assistant Sub-Inspector (Nepal Police)", organization="Nepal Police",
         category="loksewa", deadline=date.today()+timedelta(days=8),
         apply_link="https://nepalpolice.gov.np", source="nepalpolice.gov.np",
         description="Nepal Police is recruiting Assistant Sub-Inspectors. Physical fitness and written examination required."),
    dict(title="Health Assistant", organization="Ministry of Health and Population",
         category="loksewa", deadline=date.today()-timedelta(days=3),
         apply_link="https://mohp.gov.np", source="mohp.gov.np",
         description="Health Assistant positions at district health offices across Nepal."),

    # Private
    dict(title="Software Engineer (React/Django)", organization="CloudFactory Nepal",
         category="private", deadline=date.today()+timedelta(days=15),
         apply_link="https://cloudfactory.com/jobs", source="cloudfactory.com",
         description="We are looking for a skilled Software Engineer with experience in React and Django. 2+ years experience required. Excellent salary and benefits."),
    dict(title="Marketing Manager", organization="Ncell Pvt. Ltd.",
         category="private", deadline=date.today()+timedelta(days=10),
         apply_link="https://ncell.com.np/careers", source="ncell.com.np",
         description="Ncell is hiring a Marketing Manager to lead digital and traditional marketing campaigns. MBA preferred."),
    dict(title="Data Analyst", organization="Deerwalk Institute of Technology",
         category="private", deadline=date.today()+timedelta(days=22),
         apply_link="https://deerwalk.edu.np", source="deerwalk.edu.np",
         description="Data Analyst position. Proficiency in Python, SQL, and data visualization tools required."),
    dict(title="Branch Manager", organization="Nepal Investment Mega Bank",
         category="private", deadline=date.today()+timedelta(days=7),
         apply_link="https://nimb.com.np/career", source="nimb.com.np",
         description="Branch Manager position for Kathmandu valley branches. Banking experience of 5+ years required."),

    # Scholarship
    dict(title="MPhil/PhD Scholarship 2025", organization="Tribhuvan University",
         category="scholarship", deadline=date.today()+timedelta(days=30),
         apply_link="https://tu.edu.np", source="tu.edu.np",
         description="Tribhuvan University offers fully funded MPhil and PhD scholarships for Nepali citizens in Science, Engineering, and Social Sciences."),
    dict(title="Japanese Government (MEXT) Scholarship", organization="Embassy of Japan, Kathmandu",
         category="scholarship", deadline=date.today()+timedelta(days=45),
         apply_link="https://np.emb-japan.go.jp", source="np.emb-japan.go.jp",
         description="MEXT Scholarship for undergraduate and graduate studies in Japan. Covers tuition, accommodation, and monthly stipend."),
    dict(title="Fulbright Foreign Student Program", organization="US Embassy Nepal",
         category="scholarship", deadline=date.today()+timedelta(days=60),
         apply_link="https://np.usembassy.gov", source="np.usembassy.gov",
         description="The Fulbright Program offers grants for graduate study and research in the United States for Nepali citizens."),

    # Foreign Employment
    dict(title="Construction Workers (Qatar)", organization="Al-Badr Construction WLL",
         category="foreign", deadline=date.today()+timedelta(days=14),
         apply_link="https://dofe.gov.np", source="dofe.gov.np",
         description="Urgent requirement for construction workers in Qatar. Free food, accommodation and medical. Salary: QAR 1200-1500/month."),
    dict(title="Housekeeping Staff (UAE)", organization="Emirates Group",
         category="foreign", deadline=date.today()+timedelta(days=9),
         apply_link="https://dofe.gov.np", source="dofe.gov.np",
         description="Housekeeping positions at 5-star hotels in Dubai. 2-year contract with renewal option. Competitive salary + benefits."),
    dict(title="Security Guard (Malaysia)", organization="G4S Security Malaysia",
         category="foreign", deadline=date.today()+timedelta(days=3),
         apply_link="https://dofe.gov.np", source="dofe.gov.np",
         description="Security Guard positions in Kuala Lumpur. DOFE approved company. MYR 1500/month + overtime."),
]


class Command(BaseCommand):
    help = 'Seed sample job listings'

    def handle(self, *args, **kwargs):
        count = 0
        for data in SAMPLE_JOBS:
            job, created = Job.objects.get_or_create(
                title=data['title'],
                organization=data['organization'],
                defaults=data
            )
            if created:
                count += 1
        self.stdout.write(self.style.SUCCESS(f'Created {count} sample jobs.'))
