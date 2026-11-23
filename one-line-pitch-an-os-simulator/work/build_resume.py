from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer

OUT = r"C:\Users\ruturaj\Documents\Codex\2026-11-21\one-line-pitch-an-os-simulator\outputs\Ruturaj_Joshi_Resume_KernelLab.pdf"

PAGE_W, PAGE_H = letter
styles = getSampleStyleSheet()
base = "Times-Roman"
bold = "Times-Bold"
italic = "Times-Italic"

title = ParagraphStyle("title", fontName=base, fontSize=25, leading=27, alignment=1, spaceAfter=2)
contact = ParagraphStyle("contact", fontName=base, fontSize=8.8, leading=11, alignment=1, spaceAfter=11)
section = ParagraphStyle("section", fontName=base, fontSize=11.2, leading=12.5, spaceBefore=4, spaceAfter=1, textTransform="uppercase")
entry = ParagraphStyle("entry", fontName=bold, fontSize=9.4, leading=11.2, spaceBefore=3, spaceAfter=0)
sub = ParagraphStyle("sub", fontName=italic, fontSize=8.7, leading=10.2, spaceAfter=1)
body = ParagraphStyle("body", fontName=base, fontSize=8.65, leading=10.3, leftIndent=14, firstLineIndent=-10, spaceAfter=1.2)
skills = ParagraphStyle("skills", fontName=base, fontSize=8.65, leading=10.3, leftIndent=0, spaceAfter=0)

def p(text, style):
    return Paragraph(text, style)

def section_block(story, label):
    story.append(p(label.upper(), section))
    story.append(HRFlowable(width="100%", thickness=0.35, color=HexColor("#111111"), spaceAfter=2))

def bullet(text):
    return p("- " + text, body)

doc = SimpleDocTemplate(OUT, pagesize=letter, leftMargin=0.66*inch, rightMargin=0.66*inch, topMargin=0.41*inch, bottomMargin=0.38*inch)
story = []
story.append(p("RUTURAJ ABHIJEET JOSHI", title))
story.append(p("+91 9172094719 | ruturajajoshi2006@gmail.com | Pune, Maharashtra, India<br/>github.com/playful-sound343", contact))

section_block(story, "Education")
story.append(p("Pune Institute of Computer Technology <font name='Times-Roman'>| Pune, India</font>", entry))
story.append(p("B.Tech in Electronics and Telecommunication Engineering, Minor in Software Development <font name='Times-Roman'>| Expected May 2028</font>", sub))
story.append(bullet("<b>CGPA:</b> 8.33/10 | <b>Coursework:</b> Machine Learning, Data Structures, Embedded Processors, Digital Signal Processing"))
story.append(p("P. B. Jog Junior College <font name='Times-Roman'>| Pune, India</font>", entry))
story.append(p("Higher Secondary Certificate | 75.83% <font name='Times-Roman'>| 2024</font>", sub))
story.append(p("Kalmadi High School <font name='Times-Roman'>| Pune, India</font>", entry))
story.append(p("Secondary School Certificate | 93.60% <font name='Times-Roman'>| 2022</font>", sub))

section_block(story, "Experience")
story.append(p("AI/ML Intern <font name='Times-Roman'>| Jun 2025 - Jul 2025</font>", entry))
story.append(p("IEEE EMBS | Biomedical imaging and machine-learning research internship <font name='Times-Roman'>| Pune, India</font>", sub))
story.append(bullet("Built a four-class Alzheimer's MRI classifier with ResNet50 transfer learning across 1,574 MRI images."))
story.append(bullet("Evaluated a 160-image held-out split: <b>76.25% accuracy</b>, 76.05% balanced accuracy, 76.56% macro-F1, and 92.64% macro one-vs-rest ROC-AUC."))
story.append(bullet("Developed a FastAPI service with secure uploads, class probabilities, Grad-CAM, Swagger documentation, health endpoints, and SQLite prediction storage."))

section_block(story, "Projects")
story.append(p("KernelLab: Operating Systems Simulator <font name='Times-Roman'>| GitHub</font>", entry))
story.append(p("Python, FastAPI, SQLite, psutil, Chart.js, Docker, pytest", sub))
story.append(bullet("Built a pure-Python OS lab with FCFS, SJF, SRTF, Round Robin, and Priority scheduling; contiguous and Buddy allocation; FIFO, LRU, Clock, and Optimal paging; Banker's safety check, wait-for graph DFS, and synchronization simulations."))
story.append(bullet("Persisted workloads, runs, metrics, and events in SQLite; exposed <b>/run</b>, <b>/history</b>, <b>/compare</b>, and <b>/stats</b> APIs with SQL aggregation and window-function rankings; containerized with non-root Docker Compose deployment."))
story.append(bullet("Captured <b>449 live Windows processes</b> and normalized CPU/RSS data into workloads: Best Fit cut external fragmentation from <b>79.4% to 58.8%</b> versus First Fit; SJF/SRTF reduced average waiting time <b>69.1%</b> versus FCFS."))

story.append(p("Transactional Double-Entry Wallet Engine <font name='Times-Roman'>| GitHub</font>", entry))
story.append(p("Python, FastAPI, PostgreSQL, SQLAlchemy, Redis, Celery, RabbitMQ, Docker", sub))
story.append(bullet("Implemented append-only double-entry accounting with PostgreSQL aggregates and exactly two ledger entries per transfer."))
story.append(bullet("Serialized transfers with transactions and SELECT FOR UPDATE locks; validated 500 concurrent transfers with <b>0 negative balances</b> and <b>0 balance discrepancies</b>."))
story.append(bullet("Added JWT authentication, Redis idempotency/rate limiting, transactional-outbox webhooks, and Celery/RabbitMQ workers."))

story.append(p("Spectral and Corruption Robustness of ResNet34 and Vision Transformers <font name='Times-Roman'>| GitHub</font>", entry))
story.append(p("PyTorch, ResNet34, ViT-S/16, Sentinel-2, EuroSAT", sub))
story.append(bullet("Fine-tuned ResNet34 and ViT-S/16 on 13-band EuroSAT (27,000 Sentinel-2 patches; 10 classes), reaching <b>96.29%</b> and <b>94.45%</b> clean test accuracy."))
story.append(bullet("Stress-tested band dropout, signal-dependent noise, and haze; applied paired t-tests with Benjamini-Hochberg FDR control across 27 conditions."))

section_block(story, "Technical Skills")
story.append(p("<b>Languages:</b> Python, C++, SQL<br/><b>Machine Learning:</b> PyTorch, scikit-learn, Deep Learning, Computer Vision<br/><b>Backend &amp; Tools:</b> FastAPI, REST APIs, SQLite, PostgreSQL, Redis, Celery, RabbitMQ, Docker, Git<br/><b>Fundamentals:</b> Data Structures and Algorithms, Operating Systems, SQL", skills))

section_block(story, "Certifications, Achievements & Volunteering")
story.append(p("<b>Certification:</b> IEEE EMBS Student Internship Program, 2025<br/><b>Achievement:</b> Finalist, Code the Cause, 2026<br/><b>Problem Solving:</b> 170+ data structures and algorithms problems solved<br/><b>Volunteering:</b> Environmental Volunteer, Forengers, Pune (2025 - Present); supported tree-plantation and public-area clean-up drives involving 200+ saplings", skills))

doc.build(story)
print(OUT)
