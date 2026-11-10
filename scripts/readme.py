"""Write README.md. Card artwork comes from build.py; the rest is native text."""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = "https://hassaan.space/"
MAIL = "mailto:sm.hassaan99@gmail.com"


def pic(slug, alt, href=None):
    s = f"""<picture>
  <source media="(max-width: 600px) and (prefers-color-scheme: dark)" srcset="art/{slug}-mobile-dark.svg">
  <source media="(max-width: 600px)" srcset="art/{slug}-mobile-light.svg">
  <source media="(prefers-color-scheme: dark)" srcset="art/{slug}-dark.svg">
  <img src="art/{slug}-light.svg" alt="{alt}" width="100%">
</picture>"""
    if href:
        s = f'<a href="{href}">\n{s}\n</a>'
    return f"<p>\n{s}\n</p>"


PROJECTS = [  # in the site's order
    ("global-health", "https://www.myglobalhealth.online/",
     "Live sites, 12 in total. Global Health. Online doctor visits in six countries. Lead software engineer since Dec 2025."),
    ("endifaa", "https://endifaa.com/",
     "Endifaa. A sports-academy platform in English and Arabic. Full-stack developer, Oct 2025 to Jun 2026."),
    ("jordy", "https://hirejordy.com/",
     "Jordy. An AI sales rep that finds buyers and books meetings. Co-founder since Mar 2026."),
    ("aertonic", "https://aertonic.com/",
     "Aertonic. Books qualified B2B sales meetings and only charges for the ones that happen. Founding engineer since Nov 2025."),
    ("zaofi", "https://zaofi.com/",
     "Zao Fi. A stock AI that turns whale, insider and Congress trades into a 0 to 100 conviction score. Founding engineer."),
]

README = f"""{pic("hero", "A pixel football match from hassaan.space: two players and one ball. Syed Muhammad Hassaan, AI engineer and full-stack software developer. Lead Software Engineer at Global Health. Karachi, Pakistan. sm.hassaan99@gmail.com. Available for freelance projects.", SITE)}

<p align="center">
  <a href="{SITE}"><b>Portfolio ↗</b></a> &nbsp;·&nbsp;
  <a href="https://www.linkedin.com/in/syed-muhammad-hassaan/"><b>LinkedIn ↗</b></a> &nbsp;·&nbsp;
  <a href="https://ryzonlabs.com"><b>Ryzon Labs ↗</b></a> &nbsp;·&nbsp;
  <a href="https://ryzuntech.com/"><b>RyzunTech ↗</b></a> &nbsp;·&nbsp;
  <a href="{MAIL}"><b>Email ↗</b></a>
</p>

I design and build AI products, web platforms and automation for startups and businesses around the world: AI agents and chatbots, web apps and platforms, workflow automation, and websites built to rank.

<p>
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/Brxerq/Brxerq/output/activity-dark.svg">
  <img src="https://raw.githubusercontent.com/Brxerq/Brxerq/output/activity-light.svg" alt="My GitHub contributions over the past year, redrawn every day." width="100%">
</picture>
</p>

{pic("experience", "Experience, as a timeline from 2024 to now. Global Health, lead software engineer since Dec 2025. Jordy, co-founder since Mar 2026. Aertonic, founding engineer since Nov 2025. Zao Fi, founding engineer since 2025. Endifaa, full-stack developer Oct 2025 to Jun 2026. Stackloom Technologies, AI and prompt engineer Jan to Sep 2025. Freelance, AI/ML engineer and web developer since Jul 2024. Quest Marketing Kuching, lead AI and software engineer Mar to Dec 2024.")}

{pic("clients", "Clients in 12 countries: Hong Kong, Malaysia, Singapore, UAE, Saudi Arabia, Czechia, Norway, Spain, Portugal, Ireland, Brazil and USA. Based in Karachi.", SITE)}

{chr(10).join(pic(s, a, h) + chr(10) for s, h, a in PROJECTS)}
<details>
<summary><b>Other work</b> · product sites, client sites and an AI CRM</summary>
<br>

| Project | What it is | Stack |
| --- | --- | --- |
| [Aerlou](https://aerlou.com/) | Product site for an AI receptionist that answers calls and texts, books appointments and syncs transcripts to the CRM | Voice AI · CRM |
| [aerlou for WhatsApp](https://chat.aerlou.com/) | Landing page and app surface for a WhatsApp assistant that files voice notes, receipts and reminders | LLMs · WhatsApp |
| [RyzunTech](https://ryzuntech.com/) | The Dubai software and AI studio where I work with a friend | Next.js · SEO |
| [Asia Pacific Dental](https://apdc.com.sg/) | In-person and virtual booking, service pages and local SEO for a Singapore dental group | Booking · Local SEO |
| [Zen Sea Yacht](https://www.zenseayacht.com.sg/) | Charter site built around fleet pages and an enquiry flow | Enquiry flow · SEO |
| [J Hair Salon](https://jhair.sg/) | Salon site with booking and service listings | Booking · SEO |
| [Surplus Alliance](https://surplusalliancehk.com/en) | Corporate site for a Hong Kong investment holding company | Corporate · Multilingual |
| Sales Navigator CRM | AI CRM on Google Play for Quest Marketing, used by 50+ people. It cut the team's manual work by 40% | Flutter · Python · OpenAI API |

</details>

<details>
<summary><b>AI experiments</b> · live demos on Hugging Face</summary>
<br>

| | Experiment | Built with |
| --- | --- | --- |
| May 2024 | **Shelf monitoring.** Real-time out-of-stock and misalignment detection for supermarket shelves, trained on 1,000 annotated images. [Live demo](https://huggingface.co/spaces/brxerq/ShelvesDetection) · [Code](https://github.com/Brxerq/Super-Market_Shelves_Detection_Object-Detection) | TensorFlow · SSD MobileNet V2 |
| Dec 2023 | **Face attendance with anti-spoofing.** Accepts only a live person: blink analysis, a hand-gesture check, phone detection and skin-texture analysis. [Live demo](https://huggingface.co/spaces/brxerq/anti-spoofing) | OpenCV · Dlib · YOLOv4 · MediaPipe |
| Mar 2023 | **Bird species classification.** 200 species from CUB-200, from a baseline CNN to a fine-tuned MobileNetV3. [Live demo](https://huggingface.co/spaces/brxerq/Bird_Classification) | TensorFlow · MobileNetV3 |

</details>

{pic("stack", "Stack. Languages: Python, TypeScript, C++, Dart. AI and data: TensorFlow, PyTorch, OpenCV, OpenAI API, LLMs and NLP. Frameworks: React, Next.js, Django and DRF, Flutter. Backend: PostgreSQL, MySQL, FastAPI, RabbitMQ. Tools: Docker, AWS, Vercel, Railway, Git. AI workflow: Claude, Codex, Antigravity, T3 Code.")}

<details>
<summary><b>Education & certifications</b></summary>
<br>

**Swinburne University of Technology** · Bachelor of Computer Science, dual major in Data Science & AI · 2021 – 2024
**Swinburne University of Technology, Sarawak** · Foundation, Information Technology / Multimedia · 2020 – 2021

- **Getting Started with AI on Jetson Nano** · NVIDIA · Aug 2025
- **Building RAG Agents with LLMs** · NVIDIA · Aug 2025
- **Fundamentals of Digital Marketing** · Google Digital Garage · Jul 2022
- **Cisco Certified Network Associate (CCNA)** · Cisco · Nov 2021

</details>

{pic("contact", "Contact. Email sm.hassaan99@gmail.com. Karachi, Pakistan, UTC+5.", MAIL)}

<p align="center">
  <a href="{MAIL}">Email</a> &nbsp;/&nbsp;
  <a href="https://www.linkedin.com/in/syed-muhammad-hassaan/">LinkedIn</a> &nbsp;/&nbsp;
  <a href="https://www.instagram.com/ha_ssaann/">Instagram</a> &nbsp;/&nbsp;
  <a href="{SITE}">Portfolio</a>
</p>
"""

if __name__ == "__main__":
    (ROOT / "README.md").write_text(README, encoding="utf-8")
