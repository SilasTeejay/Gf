import streamlit as st
import random
import time
import re
import asyncio
import os
import spacy

# --- Streamlit App Configuration and Styling ---
st.set_page_config(
    page_title="Nigeria Info Chatbot",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for white and green theme, and basic animation
st.markdown(
    """
    <style>
    /* Dominant white background for the entire app */
    .stApp {
        background-color: white;
        color: #2E8B57; /* Darker green for general text */
    }

    /* Sidebar background and text (Still kept for general Streamlit styling) */
    [data-testid="stSidebar"] {
        background-color: #F0FFF0; /* Very light green/mint */
        color: #2E8B57; /* Dark green for sidebar text */
    }

    /* Header/Title */
    h1 { /* Targeting H1 tag for the main title */
        color: #2E8B57; /* Dark green title */
        text-align: center;
        margin-bottom: 20px;
    }

    /* User chat message bubble - light green background */
    /* This targets the actual content container within the user's chat message */
    [data-testid="stChatMessage"] div.st-emotion-cache-nahz7x { /* This class is for user messages */
        background-color: #E0FFE0; /* Light green for user messages */
        border-radius: 15px;
        padding: 12px;
        margin-bottom: 8px;
        color: #1A1A1A; /* Dark text for readability */
    }

    /* Bot chat message bubble - off-white/light mint background with green border and animation */
    /* This targets the actual content container within the assistant's chat message */
    [data-testid="stChatMessage"] div.st-emotion-cache-1c7y2qn { /* This class is for assistant messages */
        background-color: #F5FFFA; /* Very light mint/off-white */
        border-left: 5px solid #2E8B57; /* Dark green accent border */
        border-radius: 15px;
        padding: 12px;
        margin-bottom: 8px;
        color: #1A1A1A; /* Dark text for readability */
        animation: fadeIn 1s ease-in-out; /* Apply fade-in animation */
    }

    /* Input widget (text input for chat) */
    /* This targets the overall container for the chat input */
    .st-emotion-cache-10qj07o { /* Common class for the text input container */
        background-color: white; /* Ensure input area is white */
        border-top: 1px solid #2E8B57; /* Green line above input */
        padding-top: 10px;
    }
    /* This targets the actual input field */
    [data-testid="stTextInput"] input {
        border: 2px solid #2E8B57; /* Green border for input field */
        border-radius: 8px;
        padding: 10px;
        color: #2E8B57; /* Green text in input */
        background-color: white;
    }
    /* This targets the label of the input field */
    [data-testid="stTextInput"] label {
        color: #2E8B57; /* Green label for input */
    }

    /* Buttons (e.g., submit button) */
    /* This targets the "Send" button in the chat input */
    .st-emotion-cache-r42kk1 { /* Common class for buttons */
        background-color: #2E8B57; /* Dark green button */
        color: white; /* White text on button */
        border-radius: 8px;
        border: none;
        padding: 10px 20px;
        font-weight: bold;
        transition: background-color 0.3s ease; /* Smooth hover effect */
    }
    .st-emotion-cache-r42kk1:hover {
        background-color: #3CB371; /* Lighter green on hover */
        color: white;
    }

    /* General Markdown text color (for responses) */
    /* This ensures text within markdown containers (like your responses) is readable */
    .st-emotion-cache-cnbnn3 p { /* Targets paragraphs within markdown containers */
        color: #1A1A1A; /* Ensure response text is readable dark color */
    }

    /* Animation Keyframes */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Load the SpaCy English model
# This will load the model downloaded in the terminal (en_core_web_sm)
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    st.error("SpaCy model 'en_core_web_sm' not found. Please run 'python -m spacy download en_core_web_sm' in your terminal.")
    st.stop() # Stop the app if model is not found


# --- Helper functions for NLP processing ---
def preprocess_text_for_matching(text):
    """
    Tokenizes, converts to lowercase, removes stopwords, and lemmatizes the text using SpaCy.
    Returns a space-separated string of processed words.
    """
    doc = nlp(text.lower())
    processed_tokens = []
    for token in doc:
        if token.is_alpha and not token.is_stop:
            processed_tokens.append(token.lemma_)
    return " ".join(processed_tokens)

# --- NEW FUNCTION FOR FORMATTING RESPONSES ---
def format_response_text(text):
    """
    Formats the given text by splitting it into sentences and joining them with newlines.
    Uses SpaCy for robust sentence tokenization.
    """
    doc = nlp(text)
    sentences = [sent.text.strip() for sent in doc.sents]
    # Join sentences with two newlines for better visual separation
    return "\n\n".join(sentences)


# 1. Define Initial Greetings ---
INITIAL_GREETINGS = [
    "Hello there! How can I assist you today regarding the Nigerian Government?",
    "Hi, human! I'm GovFocus AI, ready to help you with information about the Nigerian Government. What's on your mind?",
    "Welcome! Ask me anything about the Nigeria Government. I'm here to provide information.",
    "Greetings! What specific information are you seeking about the Nigerian government today?"
]

# --- 2. Define User Greeting Keywords and Corresponding Assistant Responses ---
USER_GREETING_KEYWORDS = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening"]
ASSISTANT_GREETING_RESPONSES = [
    "Hello! How can I help you with information about the Nigerian government?",
    "Hi there! What can I tell you about the Nigerian government today?",
    "Hey! Ask away about the Nigerian government.",
    "Greetings! What's your question regarding the Nigerian government?"
]

# --- Initialize TF-IDF Vectorizer and Process KB ---
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

RAW_KNOWLEDGE_BASE = {
    "nigerian president": "The current President of Nigeria is Bola Ahmed Tinubu.",
    "capital of nigeria": "The capital city of Nigeria is Abuja.",
    "nigerian states": "Nigeria has 36 states and the Federal Capital Territory, Abuja.",
    "nigerian population": "According to the National Population Commission, Nigeria's population is estimated to be over 200 million people.",
    "nigerian currency": "The currency of Nigeria is the Naira (NGN).",
    "functions of government": "The functions of government include maintaining law and order, providing public services, regulating the economy, and defending the nation.",
    "local government": "Local governments in Nigeria are the third tier of government, responsible for grassroots development and service delivery in specific areas.",
    "federal government": "The Federal Government of Nigeria is the central governing body, with responsibilities for national defense, foreign policy, monetary policy, and major infrastructure projects.",
    "state government": "State governments in Nigeria are responsible for governance within their respective states, including education, healthcare, and state-level infrastructure.",
    "Nigeria History Overview": """
    Nigeria's history is rich and diverse, spanning millennia from ancient civilizations to its modern nation-state.
    Pre-colonial era: Various sophisticated empires and kingdoms flourished, such as the Nok civilization (5th century BC to 2nd century AD) known for its terracotta sculptures, the Kanem-Bornu Empire (9th-19th century AD) in the North-East, the Hausa city-states (from 11th century AD) in the North, and the Yoruba kingdoms of Ife (11th-15th century) and Oyo (16th-18th century) in the Southwest. The Benin Empire (15th-19th century) in the South-South was renowned for its bronze artistry and extensive trade networks, particularly with the Portuguese who arrived in the late 15th century.
    Colonial Era (19th Century - 1960):
    * **1800s:** The British gradually increased their influence, driven by trade (palm oil, rubber) and the abolition of the slave trade. The Lagos Colony was established in 1861.
    * **1884-1885:** At the Berlin Conference, European powers formally partitioned Africa, and Britain was granted control over the territory that would become Nigeria.
    * **1900:** The Protectorates of Northern and Southern Nigeria were established.
    * **1914:** The Northern and Southern Protectorates were amalgamated by Lord Frederick Lugard, forming the Colony and Protectorate of Nigeria. This act unified diverse ethnic groups under a single colonial administration, laying the foundation for the modern Nigerian state.
    * **Mid-20th Century:** A growing nationalist movement emerged, with key figures like Nnamdi Azikiwe, Obafemi Awolowo, and Ahmadu Bello advocating for self-governance.

    Independence and Post-Independence:
    * **October 1, 1960:** Nigeria gained full independence from British rule, becoming a federation. Alhaji Abubakar Tafawa Balewa became the first Prime Minister.
    * **1963:** Nigeria became a republic, with Nnamdi Azikiwe as its first President.
    * **1966:** Two military coups occurred, leading to widespread unrest and ethnic tensions.
    * **1967-1970:** The Nigerian Civil War (Biafran War) erupted when the Eastern Region seceded, forming the Republic of Biafra. The war resulted in millions of deaths, primarily from starvation, and ended with Biafra's reintegration into Nigeria.
    * **1970-1979:** A period of military rule followed the civil war, marked by an oil boom, but also corruption and political instability.
    * **1979-1983:** The Second Republic, a brief return to civilian rule under President Shehu Shagari, ended with another military coup.
    * **1983-1999:** A protracted period of military dictatorships, including the regimes of Muhammadu Buhari, Ibrahim Babangida, and Sani Abacha. This era was characterized by human rights abuses, economic hardship, and political repression, including the annulment of the 1993 presidential election results.
    * **1999:** A transition to democratic civilian rule occurred with the election of Olusegun Obasanjo as President, marking the beginning of the Fourth Republic. This ushered in a period of sustained democracy, though challenges like corruption, insecurity, and economic diversification persist.
    """,
    "National Anthem of Nigeria": """
    Nigeria currently uses "Nigeria, We Hail Thee" as its national anthem, readopted on May 29, 2024.
    The lyrics are:

    **Verse 1:**
    Nigeria, we hail thee,
    Our own dear native land,
    Though tribe and tongue may differ,
    In brotherhood, we stand,
    Nigerians all, and proud to serve
    Our sovereign Motherland.

    **Verse 2:**
    Our flag shall be a symbol
    That truth and justice reign,
    In peace or battle honour'd,
    And this we count as gain,
    To hand on to our children
    A banner without stain.

    **Verse 3:**
    O God of all creation,
    Grant this our one request,
    Help us to build a nation
    Where no man is oppressed,
    And so with peace and plenty,
    Nigeria may be blessed.
    """,
    "Current Governors of Nigerian States (as of May 2025)": """
    * **Abia State:** Alex Otti (Labour Party)
    * **Adamawa State:** Ahmadu Umaru Fintiri (PDP)
    * **Akwa Ibom State:** Umo Eno (PDP)
    * **Anambra State:** Charles Soludo (APGA)
    * **Bauchi State:** Bala Muhammed (PDP)
    * **Bayelsa State:** Douye Diri (PDP)
    * **Benue State:** Hyacinth Alia (APC)
    * **Borno State:** Babagana Zulum (APC)
    * **Cross River State:** Bassey Otu (APC)
    * **Delta State:** Sheriff Oborevwori (APC)
    * **Ebonyi State:** Francis Nwifuru (APC)
    * **Edo State:** Monday Okpebholo (APC)
    * **Ekiti State:** Biodun Oyebanji (APC)
    * **Enugu State:** Peter Mbah (PDP)
    * **Gombe State:** Muhammad Inuwa Yahaya (APC)
    * **Imo State:** Hope Uzodinma (APC)
    * **Jigawa State:** Umar Namadi (APC)
    * **Kaduna State:** Uba Sani (APC)
    * **Kano State:** Abba Kabir Yusuf (New Nigeria Peoples Party - NNPP)
    * **Katsina State:** Dikko Umaru Radda (APC)
    * **Kebbi State:** Nasir Idris (APC)
    * **Kogi State:** Ahmed Usman Ododo (APC)
    * **Kwara State:** AbdulRahman AbdulRazaq (APC)
    * **Lagos State:** Babajide Sanwo-Olu (APC)
    * **Nasarawa State:** Abdullahi Sule (APC)
    * **Niger State:** Mohammed Umar Bago (APC)
    * **Ogun State:** Dapo Abiodun (APC)
    * **Ondo State:** Lucky Aiyedatiwa (APC)
    * **Osun State:** Ademola Adeleke (PDP)
    * **Oyo State:** Seyi Makinde (PDP)
    * **Plateau State:** Caleb Mutfwang (PDP)
    * **Rivers State:** Siminalayi Fubara (PDP)
    * **Sokoto State:** Ahmad Aliyu (APC)
    * **Taraba State:** Agbu Kefas (PDP)
    * **Yobe State:** Mai Mala Buni (APC)
    * **Zamfara State:** Dauda Lawal (PDP)
    * **Federal Capital Territory (Minister):** Nyesom Wike (APC) - *Note: FCT is administered by a Minister, not a Governor.*
    """,
    "Achievements in Nigeria's Education Sector": """
    Nigeria's education sector has seen significant efforts and achievements aimed at expanding access, improving quality, and integrating technology.

    * **Mass Reintegration of Out-of-School Children:** A major recent achievement (reported in early 2025) is the successful reintegration of over four million out-of-school children into educational institutions within a single year. This was achieved through strategic policies like the DOTS framework (Data Repository, Out-of-School Education, Teacher Training and Development, and Skills Acquisition), with ongoing plans to enroll millions more annually. [Source: URNI Post, May 2025](https://unveilingnigeria.ng/post/nigeria-achieves-milestone-education-4-million-out-school-children-back-class)
    * **Increased Enrollment Rates:** School enrollment has surged significantly from 30 million to 55 million learners, demonstrating increased access to basic and tertiary education. This includes a notable increase in enrollment for learners with disabilities (200,500 learners). [Source: URNI Post, May 2025](https://unveilingnigeria.ng/post/nigeria-achieves-milestone-education-4-million-out-school-children-back-class)
    * **Student Loan Program:** The National Education Loan Fund (NELFUND) has been established to provide financial support to students. As of early 2025, NELFUND has disbursed 3 billion naira to support students, easing the financial burden on students and their families. [Source: URNI Post, May 2025](https://unveilingnigeria.ng/post/nigeria-achieves-milestone-education-4-million-out-school-children-back-class)
    * **Teacher Training and Development:** More than 85,662 teaching and non-teaching staff have received training, aiming to improve pedagogical methods and overall educational delivery. [Source: URNI Post, May 2025](https://unveilingnigeria.ng/post/nigeria-achieves-milestone-education-4-million-out-school-children-back-class)
    * **Infrastructure Development in Institutions:**
        * The Universal Basic Education Commission (UBEC) has provided over 40,000 new facilities for basic and senior secondary education.
        * The Tertiary Education Trust Fund (TETFUND) has contributed more than 6,500 facilities to higher education institutions, enhancing learning environments. [Source: URNI Post, May 2025](https://unveilingnigeria.ng/post/nigeria-achieves-milestone-education-4-million-out-school-children-back-class)
    * **Establishment of Tertiary Institutions:** Historically, Nigeria has seen the establishment of numerous federal and state universities, significantly expanding higher education access. Notable examples include:
        * University of Nigeria, Nsukka (established 1960)
        * Obafemi Awolowo University, Ile-Ife (established 1962, formerly University of Ife)
        * Ahmadu Bello University, Zaria (established 1962)
        * Establishment of specialized Universities of Technology and Agriculture under various administrations to focus on technical and vocational skills. [Source: Excellence and Education Network](https://exced.ucoz.com/index/legends_in_nigerian_education/0-162)
    * **Transnational Education (TNE) System:** The introduction of TNE is opening doors for Nigerian scholars to access world-class education at reduced costs and attracting foreign investments into the sector. [Source: URNI Post, May 2025](https://unveilingnigeria.ng/post/nigeria-achieves-milestone-education-4-million-out-school-children-back-class)
    * **Integration of Technology:** Artificial intelligence and other technological innovations are being adopted to enhance teaching and learning processes, pushing for a more digitally-driven education system. [Source: URNI Post, May 2025](https://unveilingnigeria.ng/post/nigeria-achieves-milestone-education-4-million-out-school-children-back-class)
    * **Increased Intake Capacity in Health Professional Education:** Enrollment quotas for medical schools, nursing schools, and other health professional training institutions have significantly increased from 28,000 to 64,000 annually to address the health workforce shortage. [Source: FMOHSW Ministerial Briefing, May 2024](https://fmino.gov.ng/achievements-in-the-health-sector-presentation-by-the-hon-cmhsw-muhammad-ali-pate-con-at-the-ministerial-sectoral-briefing-radio-house-abuja-may-24-2024/)
    """,
    "Achievements in Nigeria's Agriculture Sector": """
    Agriculture remains a cornerstone of the Nigerian economy, with various policies and initiatives aimed at boosting food security, creating jobs, and increasing exports.

    * **Contribution to GDP and Employment:** Agriculture contributed about 19.63% of Nigeria's Gross Domestic Product (GDP) in 2023 and accounted for over 35% of total employment, providing livelihoods for most Nigerians. [Source: VON, Oct 2024](https://von.gov.ng/driving-nigerias-agricultural-productivity-through-policies-programmes-and-projects-since-1960/)
    * **Major Global Producer:** Nigeria is a leading global producer of several key crops (2022 data):
        * **Cassava:** World's largest producer (59.6 million tons).
        * **Yam:** World's largest producer (47.5 million tons).
        * **Taro:** World's largest producer (3.3 million tons).
        * **Cowpea:** World's largest producer (2.6 million tons).
        * **Sorghum:** World's largest producer (6.8 million tons).
        * Significant producer of okra (2nd), peanut (3rd), sweet potato (3rd), ginger (3rd), millet (4th), palm oil (4th), sesame seed (4th), and cocoa (4th). [Source: Wikipedia - Agriculture in Nigeria](https://en.wikipedia.org/wiki/Agriculture_in_Nigeria)
    * **Export Rate and Revenue:** While specific recent export revenue figures for the entire sector are dynamic, efforts are geared towards increasing agro-produce exports. For instance, Lagos State is actively encouraging and supporting agripreneurs to export produce. The overall strategy includes driving agricultural growth to contribute to food security, self-sufficiency, and exports to Africa and the world. [Source: NAN News, May 2025](https://nannews.ng/2025/05/23/lagos-lists-achievements-in-agriculture-woos-young-agriprenuers-through-agrinnovation/)
    * **Policy Reforms and Programmes:**
        * **National Accelerated Food Production Programme (NAFPP, 1973):** Encouraged increased food production through modern agricultural practices.
        * **Operation Feed the Nation (OFN, 1976):** Promoted individual and group food production, subsidized fertilizers, constructed storage facilities, and subsidized land preparation and agrochemicals. It significantly raised awareness of agriculture's role in food security.
        * **Agricultural Transformation Agenda Support Programme (2011):** Focused on revitalizing the sector, driving income growth, and achieving food and nutritional security.
        * **Agricultural Promotion Policy (APP) / Green Alternative (2016-2020):** Aimed at improving farmers' access to loans, upscaling production skills, and increasing acreage, with special investments in rice production (e.g., Anchor Borrowers' Programme).
        * **National Agricultural Growth Scheme – Agro-Pocket (NAGS-AP):** Designed to stimulate increased productivity and higher yields, ensuring a significant impact on food production under the current administration. [Source: VON, Oct 2024](https://von.gov.ng/driving-nigerias-agricultural-productivity-through-policies-programmes-and-projects-since-1960/)
    * **Private Sector Engagement and Agrinnovation:**
        * Lagos State, for instance, has actively wooed young agripreneurs through initiatives like the "Agrinnovation Club" and "Lagos Agrithon," providing grants (e.g., over N100 million to 26 businesses in 2024) and fostering collaboration to modernize food systems and attract youth to agriculture. [Source: NAN News, May 2025](https://nannews.ng/2025/05/23/lagos-lists-achievements-in-agriculture-woos-young-agriprenuers-through-agrinnovation/)
    * **Livestock Production:** Occupies a central position with significant numbers of poultry (over 80 million), goats (76 million), sheep (43.4 million), cattle (18.4 million), and pigs (7.5 million) as of 2017 data. [Source: Wikipedia - Agriculture in Nigeria](https://en.wikipedia.org/wiki/Agriculture_in_Nigeria)
    """,
    "Achievements in Nigeria's Technology Sector": """
    Nigeria's technology sector is rapidly growing, positioning the country as a significant player in Africa's digital economy, driven by mobile connectivity, innovation, and a vibrant startup ecosystem.

    * **Mobile Connectivity and Digitalization:** Nigeria has witnessed an unprecedented surge in digitalization, with mobile network access assuming a pivotal role. This includes widespread adoption of 4G technology and the nation stepping into the 5G era, facilitated by government strategy to leverage digital technology for economic diversification. [Source: Ericsson Blog, Aug 2023](https://www.ericsson.com/en/blog/middle-east-africa/2023/unleashing-sustainable-digital-transformation-in-nigeria)
    * **Growth of FinTech:** Mobile money is playing a pivotal role in enhancing financial resilience, driving higher savings, and fostering financial inclusion for the unbanked. The Central Bank of Nigeria's introduction of Payment Service Bank (PSB) licenses has catalyzed massive growth in registered agents and expanded mobile financial services. Financial technologies like USSD, e-payment features, and two-factor authentication have made transactions infinitely safer and more secure. Nigeria's tech startups attracted $5.2 billion in venture capital in 2022, with West Africa (led by Nigeria) accounting for the largest share. [Source: Tony Elumelu Foundation, Apr 2023](https://www.tonyelumelufoundation.org/wp-content/uploads/dlm_uploads/2022/08/The-Future-of-Technology-and-Innovation-in-Nigeria.pdf)
    * **Tech Startup Ecosystem:** Nigeria is becoming the destination for Africa's promising tech startups. The country has seen the emergence of several "unicorns" (startups valued over $1 billion), particularly in the FinTech space (e.g., Flutterwave, Paystack, Interswitch). [Source: Tony Elumelu Foundation, Apr 2023](https://www.tonyelumelufoundation.org/wp-content/uploads/dlm_uploads/2022/08/The-Future-of-Technology-and-Innovation-in-Nigeria.pdf)
    * **Remote and Hybrid Work Transformation:** Over 65% of Nigerian respondents in a recent Ericsson ConsumerLab study engage in remote work at least once a week, relying on mobile broadband solutions (3G/4G/5G routers or smartphone tethering) for home connectivity, indicating a profound transformation in the workplace. [Source: Ericsson Blog, Aug 2023](https://www.ericsson.com/en/blog/middle-east-africa/2023/unleashing-sustainable-digital-transformation-in-nigeria)
    * **Digital Transformation in Public and Private Sectors:** Banks have implemented Open Digital Banking platforms and paperless initiatives. For example, UBA's Leo chatbot became a digital persona for automated service across social media platforms. [Source: Tony Elumelu Foundation, Apr 2023](https://www.tonyelumelufoundation.org/wp-content/uploads/dlm_uploads/2022/08/The-Future-of-Technology-and-Innovation-in-Nigeria.pdf)
    * **Digital Identity and Financial Inclusion:** Initiatives like the National Identification Number (NIN) and Bank Verification Number (BVN) leverage technology to formalize identity and expand financial services.
    """,
    "Achievements in Nigeria's Health Sector": """
    Nigeria's health sector has seen significant reforms, increased investment, and targeted initiatives aimed at improving healthcare access, quality, and outcomes, particularly for vulnerable populations.

    * **Health Sector Renewal Investment Initiative (SWAp Approach):** A strategic blueprint launched by the Ministry of Health and Social Welfare (FMOHSW) to improve population health outcomes, particularly through primary healthcare and enhancing reproductive, maternal, and child health services. This includes a compact signed with all 36 states and the FCT. [Source: FMOHSW Ministerial Briefing, May 2024](https://fmino.gov.ng/achievements-in-the-health-sector-presentation-by-the-hon-cmhsw-muhammad-ali-pate-con-at-the-ministerial-sectoral-briefing-radio-house-abuja-may-24-2024/)
    * **Free Caesarean Sections:** Groundbreaking innovations like the Maternal and Newborn Mortality Reduction Initiative offer free caesarean sections to eligible Nigerian women, significantly reducing maternal and newborn mortality. [Source: Punch Newspapers, Jan 2025](https://punchng.com/a-stellar-year-for-nigerias-health-sector/)
    * **Retraining of Health Workers:** Over 53,000 frontline health workers have been retrained to deliver integrated, high-quality services. Plans are in place to equip at least 120,000 frontline health workers serving rural populations over the next three years. [Source: FMOHSW Ministerial Briefing, May 2024](https://fmino.gov.ng/achievements-in-the-health-sector-presentation-by-the-hon-cmhsw-muhammad-ali-pate-con-at-the-ministerial-sectoral-briefing-radio-house-abuja-may-24-2024/)
    * **Expanded Health Coverage (BHCPF):** The Basic Health Care Provision Fund (BHCPF) was redesigned and now covers approximately 10 million Nigerians, with a record 2.4 million citizens enrolling in the national health insurance scheme, enhancing access to affordable healthcare. [Source: Punch Newspapers, Jan 2025](https://punchng.com/a-stellar-year-for-nigerias-health-sector/)
    * **Revenue and Investment Attraction:** The sector has secured significant financing mechanisms, including a €1 billion European Investment Bank financing and a $1 billion Afreximbank financing to support incoming manufacturers in the health and life sciences sectors. Over 70 new healthcare manufacturing companies are in discussions, with 22 large-scale projects actively engaging international financiers. [Source: Punch Newspapers, Jan 2025](https://punchng.com/a-stellar-year-for-nigerias-health-sector/)
    * **Local Manufacturing Initiatives:** The Presidential Unlocking Healthcare Value Chain Initiative aims to increase local manufacturing of rapid diagnostic tests (e.g., Abbott Diagnostics plant), medical oxygen (e.g., Global Gases group plant), essential antibiotics (e.g., Jawa Investments producing Amoxicillin-Clavulanic Acid locally), vaccines, and other health solutions. [Source: Punch Newspapers, Jan 2025](https://punchng.com/a-stellar-year-for-nigerias-health-sector/)
    * **Vaccination Campaigns:** Over 5 million Nigerian children vaccinated against diphtheria, more than 10 million received tetanus and diphtheria vaccines, and over 5 million received measles vaccines. Additionally, 4.95 million girls (9-14 years) in 15 states received HPV vaccines (80% target achieved in some areas), with plans for 6 million more. [Source: FMOHSW Ministerial Briefing, May 2024](https://fmino.gov.ng/achievements-in-the-health-sector-presentation-by-the-hon-cmhsw-muhammad-ali-pate-con-at-the-ministerial-sectoral-briefing-radio-house-abuja-may-24-2024/)
    * **New Hospitals and Infrastructure:** Federal hospitals successfully executed 201 specific infrastructure projects in the last year. 179 specific pieces of important medical equipment were procured and distributed across the six geopolitical zones. At least 1,400 Primary Health Care Centers are now equipped to provide skilled birth attendance. [Source: FMOHSW Ministerial Briefing, May 2024](https://fmino.gov.ng/achievements-in-the-health-sector-presentation-by-the-hon-cmhsw-muhammad-ali-pate-con-at-the-ministerial-sectoral-briefing-radio-house-abuja-may-24-2024/)
    * **Human Resources for Health:** Over 2,400 health workers (nurses, doctors, midwives) have been recruited to provide services. The intake capacity of medical and nursing schools has significantly increased from 28,000 to 64,000 annually. [Source: FMOHSW Ministerial Briefing, May 2024](https://fmino.gov.ng/achievements-in-the-health-sector-presentation-by-the-hon-cmhsw-muhammad-ali-pate-con-at-the-ministerial-sectoral-briefing-radio-house-abuja-may-24-2024/)
    """,
    "Achievements in Nigeria's Infrastructure Sector": """
    Nigeria has been actively pursuing ambitious infrastructure projects to improve connectivity, drive economic growth, and strengthen long-term development, despite facing significant deficits.

    * **Road and Highway Expansion:** Major construction projects have improved transportation networks across the country, easing congestion and boosting trade. Significant progress has been noted in road and highway expansion in 2024, improving connectivity across urban and rural areas. [Source: The Estero, Feb 2025](https://www.olaniwunajayi.net/blog/nigerias-infrastructure-growth-in-2024-key-developments-and-2025-outlook/)
    * **Railway Upgrades and Modernization:** Expanded rail lines now connect key cities, reducing travel time and supporting economic activity. The government's commitment to modernizing transport networks aligns with long-term economic development goals. [Source: The Estero, Feb 2025](https://www.olaniwunajayi.net/blog/nigerias-infrastructure-growth-in-2024-key-developments-and-2025-outlook/)
    * **Airport Development:** Renovation and expansion of international airports (e.g., Lagos, Abuja, Kano, Port Harcourt) with new terminals, aiming to improve passenger experience and cargo handling.
    * **Port Modernization:** Efforts to modernize seaports to enhance efficiency, reduce congestion, and boost trade facilitation, including ongoing deep seaport projects like the Lekki Deep Seaport, which is expected to significantly boost cargo handling capacity.
    * **Power Sector Reforms and Projects:** Ongoing efforts to improve electricity generation, transmission, and distribution, with investments in new power plants and efforts to improve grid stability. The Presidential Power Initiative (PPI) aims to upgrade the national grid.
    * **Urban Development and Housing:** Investments in sustainable housing initiatives and smart city projects are reshaping Nigeria's urban landscape, with a focus on affordable housing. Developers are leveraging innovative construction methods to reduce costs and improve efficiency. [Source: The Estero, Feb 2025](https://www.olaniwunajayi.net/blog/nigerias-infrastructure-growth-in-2024-key-developments-and-2025-outlook/)
    * **Telecommunications Infrastructure:** Rapid growth in broadband penetration and the rollout of 5G technology in major cities have strengthened connectivity and accelerated digital transformation. Improved broadband penetration and government-backed digital inclusion initiatives are strengthening Nigeria's position as a key player in Africa's digital economy. [Source: The Estero, Feb 2025](https://www.olaniwunajayi.net/blog/nigerias-infrastructure-growth-in-2024-key-developments-and-2025-outlook/)
    * **Public-Private Partnerships (PPPs):** The government is strengthening PPP frameworks to attract private investment and ensure sustainable project financing across various infrastructure sectors. Reforms in construction regulations and land acquisition laws are part of this effort, making large-scale developments more feasible. [Source: The Estero, Feb 2025](https://www.olaniwunajayi.net/blog/nigerias-infrastructure-growth-in-2024-key-developments-and-2025-outlook/)
    * **Revival of Stalled Projects:** Commitment to completing and reviving previously stalled infrastructure projects, demonstrating dedication to continuity in development.
    * **Bridges and Flyovers:** Construction of major bridges and flyovers in urban centers (e.g., Lagos) to ease traffic congestion and improve urban mobility.
    """
    # Add more Q&A pairs here
    }


vectorizer = TfidfVectorizer(tokenizer=lambda x: x.split(), lowercase=True)


processed_kb_keys_list = [
    preprocess_text_for_matching(key)
    for key in RAW_KNOWLEDGE_BASE.keys()
]


kb_vectors = vectorizer.fit_transform(processed_kb_keys_list)

KB_ENTRIES_FOR_MATCHING = list(RAW_KNOWLEDGE_BASE.items())

# --- 4. Function to Check for User Greetings ---
def check_for_user_greeting(query):
    query_lower = query.lower().strip() # Normalize input
    for keyword in USER_GREETING_KEYWORDS:
        # Check if the query starts with the greeting keyword (and optional punctuation/space)
        if query_lower.startswith(keyword):
            # Further check to ensure it's not part of a larger word
            remaining_part = query_lower[len(keyword):].strip()
            if not remaining_part or remaining_part[0] in [' ', ',', '.', '!', '?']: # If empty or followed by a separator
                return random.choice(ASSISTANT_GREETING_RESPONSES)
    return None

# --- 5. Function to Search Knowledge Base (using TF-IDF and Cosine Similarity) ---
def get_response_from_kb(query, similarity_threshold=0.3): # Adjust threshold as needed
    processed_user_query_str = preprocess_text_for_matching(query)

    # TEMPORARY DEBUGGING PRINTS (will appear in Codespaces terminal/logs)
    print(f"\n--- KB Matching Debug ---")
    print(f"User Query (Raw): {query}")
    print(f"User Query (Processed): '{processed_user_query_str}'")

    if not processed_user_query_str.strip():
        print("No meaningful words in processed user query.")
        return None

    try:
        user_query_vector = vectorizer.transform([processed_user_query_str])
    except ValueError as e:
        print(f"ERROR: Could not transform user query '{processed_user_query_str}'. This might mean the query has no words from the KB vocabulary. Error: {e}")
        return None

    similarity = cosine_similarity(user_query_vector, kb_vectors)

    best_match_index = similarity.argmax()
    highest_similarity_score = similarity[0, best_match_index]

    print(f"Highest Similarity Score: {highest_similarity_score:.2f}")

    if highest_similarity_score > 0 and best_match_index < len(KB_ENTRIES_FOR_MATCHING):
        matched_kb_original_key = KB_ENTRIES_FOR_MATCHING[best_match_index][0]
        print(f"Matching KB Original Key: {matched_kb_original_key}")
        print(f"Matching KB Processed Key: {processed_kb_keys_list[best_match_index]}")
    else:
        print(f"No match found or best_match_index out of bounds/zero similarity.")


    if highest_similarity_score >= similarity_threshold:
        return KB_ENTRIES_FOR_MATCHING[best_match_index][1]

    print(f"No significant KB match found above threshold ({similarity_threshold:.2f}).")
    return None

# --- Streamed response emulator (ASYNCHRONOUS) ---
async def response_generator(response_text):
    for word in response_text.split():
        yield word + " "
        await asyncio.sleep(0.05)

st.title("🇳🇬 GovFocus AI: Your Guide to the Nigerian Government")
st.markdown("Ask me anything about the Nigerian Government.")

# --- Initialize ALL session state variables here ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.first_message_displayed = False

# --- Display initial greeting if it's the first run (and only once per session) ---
if not st.session_state.first_message_displayed:
    initial_greeting = random.choice(INITIAL_GREETINGS)
    with st.chat_message("assistant"):
        response = st.write_stream(response_generator(initial_greeting))
    st.session_state.messages.append({"role": "assistant", "content": initial_greeting})
    st.session_state.first_message_displayed = True
    st.balloons()

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"], unsafe_allow_html=True)


# Accept user input
if prompt := st.chat_input("What do you want me to talk to you about:"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt, unsafe_allow_html=True)

    # --- Determine assistant response based on hierarchy: Greeting -> KB -> Fallback ---
    assistant_response = None

    # 1. Check for user greetings first
    greeting_response = check_for_user_greeting(prompt)
    if greeting_response:
        assistant_response = greeting_response
    else:
        # 2. If no greeting, check knowledge base using processed query
        with st.spinner("Searching knowledge base..."):
            kb_raw_response = get_response_from_kb(prompt)
            if kb_raw_response:
                # Apply the new formatting function here
                assistant_response = format_response_text(kb_raw_response)
            else:
                assistant_response = None # No KB response found

    # 3. If still no response, use fallback
    if not assistant_response:
        assistant_response = "I can not respond to this now. In future iterations, I will be able to provide an answer. I am still a work in progress."

    # Display the chosen assistant response
    with st.chat_message("assistant"):
        response_stream = response_generator(assistant_response)
        response = st.write_stream(response_stream)
        st.session_state.messages.append({"role": "assistant", "content": response})
