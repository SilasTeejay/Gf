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
    layout="wide", # This is fine for desktop, Streamlit handles responsiveness for columns etc. on mobile
    initial_sidebar_state="expanded"
)

# Define a color palette for easier management
# Using a deeper green palette now
PRIMARY_DEEP_GREEN = "#006400"  # A rich, deep forest green
LIGHT_USER_GREEN = "#E0FFE0"   # Very light green for user bubbles
ACCENT_GREEN = "#3CB371"       # Medium sea green for hover states/secondary elements
# Changed this to a lighter color for text on deep green background
TEXT_ON_DEEP_GREEN = "#FFFFFF" # White text for deep green background
TEXT_DARK = "#1A1A1A"          # Very dark grey for main text (almost black)

# Custom CSS for theme and animation
st.markdown(
    f"""
    <style>
    /* Dominant white background for the entire app */
    .stApp {{
        background-color: white;
        color: {PRIMARY_DEEP_GREEN}; /* Deep green for general text */
    }}

    /* Sidebar background and text */
    [data-testid="stSidebar"] {{
        background-color: {TEXT_ON_DEEP_GREEN}; /* Use white for sidebar background */
        color: {PRIMARY_DEEP_GREEN}; /* Deep green for sidebar text */
    }}

    /* Header/Title */
    h1 {{
        color: {PRIMARY_DEEP_GREEN}; /* Deep green title */
        text-align: center;
        margin-bottom: 20px;
    }}

    /* User chat message bubble */
    [data-testid="stChatMessage"] div.st-emotion-cache-nahz7x {{ /* This class is for user messages */
        background-color: {LIGHT_USER_GREEN}; /* Light green for user messages */
        border-radius: 15px;
        padding: 12px;
        margin-bottom: 8px;
        color: {TEXT_DARK}; /* Ensure user message text is dark for readability */
        word-wrap: break-word; /* Crucial for mobile: breaks long words */
    }}

    /* Bot (Assistant) chat message bubble */
    /* Increased specificity and !important for background and text color */
    [data-testid="stChatMessage"] div.st-emotion-cache-1c7y2qn,
    [data-testid="stChatMessage"] div.st-emotion-cache-1c7y2qn p,
    [data-testid="stChatMessage"] div.st-emotion-cache-1c7y2qn ol,
    [data-testid="stChatMessage"] div.st-emotion-cache-1c7y2qn ul,
    [data-testid="stChatMessage"] div.st-emotion-cache-1c7y2qn li {{
        background-color: {PRIMARY_DEEP_GREEN} !important; /* Set background to deep green and force it */
        color: {TEXT_ON_DEEP_GREEN} !important; /* Force white text color for readability */
    }}

    [data-testid="stChatMessage"] div.st-emotion-cache-1c7y2qn {{ /* Targeting the main container again for other properties */
        border-left: 5px solid {ACCENT_GREEN}; /* Accent green border */
        border-radius: 15px;
        padding: 12px;
        margin-bottom: 8px;
        animation: fadeIn 1s ease-in-out;
        word-wrap: break-word; /* Crucial for mobile: breaks long words */
    }}

    /* Input widget (text input for chat) */
    .st-emotion-cache-10qj07o {{ /* Common class for the text input container */
        background-color: white;
        border-top: 1px solid {PRIMARY_DEEP_GREEN}; /* Deep green line above input */
        padding-top: 10px;
    }}
    [data-testid="stTextInput"] input {{
        border: 2px solid {PRIMARY_DEEP_GREEN}; /* Deep green border for input field */
        border-radius: 8px;
        padding: 10px;
        color: {PRIMARY_DEEP_GREEN}; /* Deep green text in input */
        background-color: white;
    }}
    [data-testid="stTextInput"] label {{
        color: {PRIMARY_DEEP_GREEN}; /* Deep green label for input */
    }}

    /* Buttons (e.g., submit button) */
    .st-emotion-cache-r42kk1 {{ /* Common class for buttons */
        background-color: {PRIMARY_DEEP_GREEN}; /* Deep green button */
        color: white; /* White text on button */
        border-radius: 8px;
        border: none;
        padding: 10px 20px;
        font-weight: bold;
        transition: background-color 0.3s ease;
    }}
    .st-emotion-cache-r42kk1:hover {{
        background-color: {ACCENT_GREEN}; /* Lighter green on hover */
        color: white;
    }}

    /* General Markdown text color (for overall app text if not in chat bubbles) */
    .st-emotion-cache-cnbnn3 p {{
        color: {TEXT_DARK} !important; /* Ensure general text is readable dark color */
    }}

    /* Animation Keyframes */
    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(10px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# Load the SpaCy English model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    st.error("SpaCy model 'en_core_web_sm' not found. Please run 'python -m spacy download en_core_web_sm' in your terminal.")
    st.stop()


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

import spacy

# Load the English language model
nlp = spacy.load("en_core_web_sm")

def format_response_text(text):
    # If the text explicitly contains Markdown list syntax or multiple newlines,
    # assume it's pre-formatted and return it as is.
    if "\n*" in text or "\n\n" in text:
        return text
    else:
        # Otherwise, apply sentence tokenization for better readability
        doc = nlp(text)
        sentences = [sent.text.strip() for sent in doc.sents]
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

vectorizer = TfidfVectorizer(tokenizer=lambda x: x.split(), lowercase=True)

RAW_KNOWLEDGE_BASE = {
    # Basic Information
    "nigerian president": "The current President of Nigeria is Bola Ahmed Tinubu.",
    "President of Nigeria": "The current President of Nigeria is Bola Ahmed Tinubu.",
    "capital of nigeria": "The capital city of Nigeria is Abuja.",
    "Abuja capital": "The capital city of Nigeria is Abuja.",
    "nigerian states": "Nigeria has 36 states and the Federal Capital Territory, Abuja.",
    "number of states in Nigeria": "Nigeria has 36 states and the Federal Capital Territory, Abuja.",
    "nigerian population": "According to the National Population Commission, Nigeria's population is estimated to be over 200 million people.",
    "population of Nigeria": "Nigeria's population is estimated to be over 200 million people, according to the National Population Commission.",
    "nigerian currency": "The currency of Nigeria is the Naira (NGN).",
    "currency of Nigeria": "The currency of Nigeria is the Naira (NGN).",

    
    # Nigerian History (Detailed Individual Entries)
    "History of Nigeria": """
The history of Nigeria begins with the flourishing Nok civilization between the 5th century BC and 2nd century AD,
followed by the rise of powerful entities such as the Kanem-Bornu Empire (9th–19th century), the Hausa city-states
(from the 11th century), the Yoruba kingdoms of Ife (11th–15th century) and Oyo (16th–18th century), and the Benin Empire
(15th–19th century), which engaged in extensive trade with the Portuguese from the late 15th century.

British influence grew in the 1800s through trade and the suppression of the slave trade, culminating in the establishment
of the Lagos Colony in 1861, British control after the Berlin Conference of 1884–1885, and the creation of the Northern and
Southern Protectorates in 1900, which were amalgamated in 1914 by Lord Frederick Lugard into the Colony and Protectorate
of Nigeria.

This sparked a nationalist movement in the mid-20th century led by figures like Nnamdi Azikiwe, Obafemi Awolowo, and
Ahmadu Bello, leading to independence on October 1, 1960, with Alhaji Abubakar Tafawa Balewa as the first Prime Minister,
and the establishment of a republic in 1963 with Nnamdi Azikiwe as its first President.

Following two coups in 1966 and the Biafran War (1967–1970), Nigeria entered a long era of military rule (1970–1979 and
1983–1999) punctuated by a brief civilian Second Republic (1979–1983), with this period marked by oil wealth, corruption,
repression, and the annulled 1993 presidential election, until democratic rule returned in 1999 with the election of
Olusegun Obasanjo.

This began the Fourth Republic which continues today amid persistent challenges like corruption, insecurity, and the need
for economic diversification.

Nigeria now operates a federal system with three tiers of government—federal, state, and local—each playing vital roles:
the Federal Government oversees national defense, foreign policy, monetary regulation, and major infrastructure;
State Governments handle education, healthcare, and state-level infrastructure within their regions; and
Local Governments focus on grassroots development and the delivery of basic services, all functioning collectively
to maintain law and order, provide public services, regulate the economy, and ensure the nation's overall governance and development.
""",

"Sanni Abacha": """
General Sani Abacha (20 September 1943 – 8 June 1998) was a Nigerian military officer and political leader who served as the country's de facto president from 1993 until his death in 1998. Born in Kano, Nigeria, Abacha was of Kanuri ethnicity. He received military training in Nigeria and the United Kingdom, rising through the ranks to become a full general without skipping any rank—a first in Nigerian military history.

Abacha played pivotal roles in several military coups, including the 1983 overthrow of President Shehu Shagari, which brought General Muhammadu Buhari to power, and the 1985 coup that installed General Ibrahim Babangida. In 1993, following the annulment of the June 12 presidential election and the resignation of interim leader Ernest Shonekan, Abacha seized power through a bloodless coup on November 17, establishing himself as head of state.

His regime was marked by authoritarian rule, characterized by the suppression of dissent, human rights abuses, and the detention of political opponents. Notably, the execution of environmental activist Ken Saro-Wiwa and eight others in 1995 drew international condemnation and led to Nigeria's suspension from the Commonwealth.

Economically, Abacha's government saw an increase in foreign exchange reserves and a reduction in external debt. However, his tenure was also marred by massive corruption; he and his associates were accused of embezzling billions of dollars from the national treasury, with significant sums stashed in foreign accounts.

Abacha died suddenly on June 8, 1998, in Abuja, reportedly of a heart attack. His death paved the way for a transition to civilian rule, culminating in the establishment of Nigeria's Fourth Republic in 1999.

Source: https://www.britannica.com/biography/Sani-Abacha
""",

"Bola Ahmed Tinubu": """
Bola Ahmed Adekunle Tinubu (born March 29, 1952) is a Nigerian accountant and politician who has been serving as the 16th President of Nigeria since May 29, 2023. He is a prominent figure in Nigerian politics, known for his influential role in the country's democratic development and political realignments.

Early Life and Education:

Tinubu was born in Lagos, Nigeria, into the merchant family of Abibatu Mogaji, who later became the Ìyál'ọ́jà (market leader) of Lagos. He attended St. John's Primary School in Aroloya, Lagos, and Children's Home School in Ibadan. In 1975, he moved to the United States, where he studied at Richard J. Daley College in Chicago before transferring to Chicago State University. He graduated in 1979 with a Bachelor of Science degree in Accounting, achieving summa cum laude honors. During his time in the U.S., Tinubu worked various jobs, including as a dishwasher, night security guard, and cab driver, to support himself through college.

Professional Career:

After graduating, Tinubu worked as an accountant for several American companies, including Arthur Andersen, Deloitte, and GTE Services Corporation. At Deloitte, he gained experience in auditing and management consultancy services for Fortune 500 corporations. He also worked as a consultant for Saudi Aramco's joint venture partner, National Oil, helping to establish their accounting and auditing systems. Tinubu later joined Mobil Oil Nigeria (now Seplat Energy) as a senior company executive and treasurer in the 1980s.

Political Career:

Tinubu's political career began in 1991 when he joined the Social Democratic Party (SDP). In 1992, he was elected to the Nigerian Senate, representing the Lagos West constituency during the short-lived Third Republic. Following the annulment of the June 12, 1993, presidential elections by the military regime, Tinubu became a founding member of the pro-democracy National Democratic Coalition (NADECO), advocating for the restoration of democracy and recognition of Moshood Abiola as the rightful winner of the election. Due to his activism, Tinubu went into exile in 1994, returning to Nigeria in 1998 after the death of military ruler General Sani Abacha.

Governor of Lagos State:

In the 1999 Lagos State gubernatorial election, Tinubu ran under the banner of the Alliance for Democracy (AD) and won by a wide margin. He was re-elected in 2003, serving as governor until 2007. During his tenure, Tinubu implemented various reforms aimed at improving the state's infrastructure, education, and healthcare systems. Notably, he introduced the "Jigi Bola" program, a free eye screening and surgical operation initiative for Lagosians, aimed at preventing blindness and raising awareness about eye health.

Formation of the All Progressives Congress (APC):

After leaving office, Tinubu played a crucial role in the formation of the All Progressives Congress (APC) in 2013, a merger of Nigeria's major opposition parties. The APC became a significant political force, winning the 2015 general elections and ending the 16-year rule of the People's Democratic Party (PDP). Tinubu's strategic political alliances and influence earned him the nickname "Godfather of Lagos" and solidified his status as a key political kingmaker in Nigeria.

Presidency:

In the 2023 Nigerian presidential election held on February 25, Tinubu ran as the APC candidate and won with 36.61% of the vote, defeating his closest rivals, Atiku Abubakar of the PDP and Peter Obi of the Labour Party. He was inaugurated as President on May 29, 2023. His administration has focused on implementing economic reforms, including the removal of petrol subsidies and currency devaluation, aimed at correcting market distortions and strengthening the economy in the long term. However, these measures have led to immediate challenges, such as soaring inflation and increased cost of living, prompting debates about their impact on the Nigerian populace.

Source: https://en.wikipedia.org/wiki/Bola_Tinubu
""",

"Peter Obi": """
Peter Gregory Obi (born July 19, 1961) is a Nigerian politician and businessman renowned for his commitment to fiscal prudence, transparency, and good governance. He served as the Governor of Anambra State from 2006 to 2014 and was the Labour Party's presidential candidate in the 2023 Nigerian general election.

Early Life and Education:

Peter Obi was born in Onitsha, Anambra State, Nigeria. He attended Christ the King College, Onitsha, for his secondary education. In 1980, he enrolled at the University of Nigeria, Nsukka, where he earned a Bachelor of Arts degree in Philosophy in 1984. Obi furthered his education with executive programs at prestigious institutions, including Lagos Business School, Harvard Business School, London School of Economics, Columbia Business School, and the Institute for Management Development in Switzerland.

Business Career:

Before venturing into politics, Obi had a successful career in business. He held leadership positions in several Nigerian companies, including Next International Nigeria Ltd, Guardian Express Bank Plc, and Future View Securities Ltd. His business acumen earned him recognition in the corporate sector, and he served on the boards of various financial institutions.

Political Career:

Obi's political journey began in 2003 when he contested the Anambra State gubernatorial election under the All Progressives Grand Alliance (APGA). Although the Independent National Electoral Commission (INEC) declared his opponent, Chris Ngige, the winner, Obi challenged the results in court. After a protracted legal battle, the Court of Appeal declared him the rightful winner, and he assumed office on March 17, 2006.

His tenure was marked by several challenges. In November 2006, he was impeached by the State House of Assembly, but the impeachment was overturned, and he was reinstated in February 2007. Obi's term ended in May 2007, but following a Supreme Court ruling that the tenure of a governor begins from the day of swearing-in, he resumed office and served until March 2014 after winning re-election in 2010.

As governor, Obi prioritized education, healthcare, and infrastructure development. He was known for his frugal management of state resources, leaving significant savings for his successor. His administration received accolades for improving the state's fiscal discipline and reducing debt.

2023 Presidential Election:

In May 2022, Peter Obi joined the Labour Party and became its presidential candidate for the 2023 general election. His campaign resonated with many Nigerians, especially the youth, who were drawn to his message of accountability and change. Obi's candidacy gained momentum through social media and grassroots mobilization, leading to significant support across the country.

In the election held on February 25, 2023, Obi secured 25% of the vote, coming third behind Bola Tinubu of the All Progressives Congress and Atiku Abubakar of the People's Democratic Party. He won in several states, including Lagos and Abia, showcasing his widespread appeal. Following the election, Obi and the Labour Party challenged the results, citing irregularities, but the courts upheld Tinubu's victory.

Legacy:

Peter Obi is widely regarded as a transformative figure in Nigerian politics. His emphasis on prudent governance, transparency, and citizen engagement has inspired a new wave of political consciousness among Nigerians. His 2023 presidential bid, though unsuccessful, marked a significant shift in the country's political landscape, highlighting the power of grassroots movements and the demand for accountable leadership.

Source: https://en.wikipedia.org/wiki/Peter_Obi
""",
"changes in oil and gas sector": """
Since 2023, Nigeria's oil and gas industry has undergone significant reforms aimed at revitalizing the sector, attracting investment, and enhancing production capacity. These improvements encompass policy changes, infrastructural developments, and strategic partnerships.

Policy Reforms and Regulatory Overhaul:

In 2023, the Nigerian government intensified efforts to implement the Petroleum Industry Act (PIA), which had been enacted in 2021. This act aimed to restructure the oil and gas sector by creating a more transparent and efficient regulatory framework. Key reforms included the establishment of the Nigerian Upstream Petroleum Regulatory Commission (NUPRC) and the Nigerian Midstream and Downstream Petroleum Regulatory Authority (NMDPRA), which replaced previous regulatory bodies to streamline operations and oversight.

In April 2025, President Bola Tinubu dismissed the entire board of the Nigerian National Petroleum Company Limited (NNPC) in a move signaling a commitment to reform. Bashir Ojulari, a seasoned industry executive with experience at Shell and Renaissance Africa Energy, was appointed as the new head of NNPC. This leadership change aimed to restore investor confidence and address longstanding issues of mismanagement and embezzlement within the company.

Investment and Infrastructure Developments:

The sector witnessed a resurgence in investment activities. Notably, the Dangote Petroleum Refinery, inaugurated in May 2023, began production. As Africa's largest oil refinery, it has a capacity of 650,000 barrels per day and aims to reduce Nigeria's dependency on imported petroleum products. The refinery's operations are expected to meet all of Nigeria's needs for gasoline, diesel, kerosene, and aviation jet fuel, with a portion available for export.

Additionally, the Nigerian Liquefied Natural Gas (NLNG) Train 7 project progressed, aiming to increase the NLNG Terminal's production capacity by 35%, from 22 million tonnes per annum (mtpa) to 30 mtpa. The project is expected to create approximately 52,000 jobs and represents a significant investment in Nigeria's gas sector.

Production and Operational Enhancements:

Efforts to boost oil production led to an increase in Nigeria's rig count. The Nigerian Upstream Petroleum Regulatory Commission reported that the nation's rig count reached 32, with expectations to increase to 50 by the end of 2025. This expansion is part of broader initiatives to enhance upstream activities and increase crude oil output.

Furthermore, the government's removal of the fuel subsidy in 2023, which previously cost Nigeria $10 billion annually, was a significant fiscal reform. This move aimed to reallocate resources more efficiently and attract foreign investment by demonstrating a commitment to market-driven policies.

Challenges and Outlook:

Despite these advancements, the sector continues to face challenges, including infrastructure deficits, regulatory bottlenecks, and security concerns affecting oil production and distribution. However, the government's ongoing reforms and commitment to improving the investment climate suggest a positive trajectory for Nigeria's oil and gas industry.

Sources:
- https://www.ft.com/content/88c76ae5-9eff-4ba1-ab09-09651a10c511
- https://apnews.com/article/5e465512e5ed569512ea3221d0df2c79
- https://en.wikipedia.org/wiki/Nigerian_LNG_train_7
- https://africanperceptions.org/en/2025/05/increasing-oil-rigs-a-big-score-for-nigerias-petroleum-sector-reforms/
- https://www.bracewell.com/resources/nigerias-energy-sector-looking-back-2023-and-looking-ahead-2024/
""",
"Nigeria political terrain": """
Nigeria's political history is marked by a series of significant events, transitions, and influential personalities that have shaped the nation's governance and democratic evolution.

**Pre-Colonial and Colonial Era:**

Before colonization, the region now known as Nigeria was home to various kingdoms and empires, including the Nok civilization, the Hausa city-states, the Yoruba kingdoms of Ife and Oyo, and the Benin Empire. British colonization began in the mid-19th century, culminating in the amalgamation of the Northern and Southern Protectorates in 1914, forming the Colony and Protectorate of Nigeria.

**Independence and First Republic (1960–1966):**

Nigeria gained independence from Britain on October 1, 1960. Sir Abubakar Tafawa Balewa became the first Prime Minister, leading a coalition government. Dr. Nnamdi Azikiwe served as the first Governor-General and later as the first President when Nigeria became a republic in 1963. The First Republic was characterized by regionalism and political tensions, leading to a military coup in January 1966.

**Military Rule and Civil War (1966–1970):**

Major General Johnson Aguiyi-Ironsi took power after the 1966 coup but was assassinated in a counter-coup led by Lieutenant Colonel Yakubu Gowon. Ethnic tensions escalated, leading to the secession of the Eastern Region as the Republic of Biafra in 1967. The Nigerian Civil War ensued, lasting until 1970, resulting in significant casualties and humanitarian crises.

**Second Republic (1979–1983):**

After a period of military rule, Nigeria returned to civilian governance in 1979 with the election of Alhaji Shehu Shagari as President. The Second Republic faced economic challenges and allegations of corruption, leading to another military coup in December 1983, bringing Major General Muhammadu Buhari to power.

**Military Regimes and Transition (1983–1999):**

General Buhari's regime was overthrown in 1985 by General Ibrahim Babangida, who initiated economic reforms and planned a transition to civilian rule. However, the annulment of the 1993 presidential election, widely believed to have been won by Chief Moshood Abiola, led to political unrest. An interim government was established under Ernest Shonekan but was quickly overthrown by General Sani Abacha, whose regime was marked by human rights abuses and suppression of dissent. Abacha's sudden death in 1998 paved the way for General Abdulsalami Abubakar to oversee a transition to democracy.

**Fourth Republic and Democratic Consolidation (1999–Present):**

In 1999, Nigeria returned to democratic rule with the election of Olusegun Obasanjo as President. Subsequent elections saw the presidencies of Umaru Musa Yar'Adua, Goodluck Jonathan, and Muhammadu Buhari. In 2023, Bola Ahmed Tinubu was elected President, continuing the democratic tradition. Despite challenges such as corruption, security issues, and economic diversification, Nigeria's democracy has shown resilience.

**Key Political Figures:**

- **Sir Abubakar Tafawa Balewa:** First Prime Minister of Nigeria.
- **Dr. Nnamdi Azikiwe:** First President of Nigeria.
- **Major General Johnson Aguiyi-Ironsi:** First military Head of State.
- **General Yakubu Gowon:** Led Nigeria during the Civil War.
- **Alhaji Shehu Shagari:** First executive President in the Second Republic.
- **General Muhammadu Buhari:** Military Head of State (1983–1985) and later elected President (2015–2023).
- **General Ibrahim Babangida:** Military ruler who initiated economic reforms.
- **Chief Moshood Abiola:** Presumed winner of the annulled 1993 election.
- **General Sani Abacha:** Military ruler known for authoritarian governance.
- **General Abdulsalami Abubakar:** Oversaw the transition to democracy in 1999.
- **Olusegun Obasanjo:** Former military ruler and elected President (1999–2007).
- **Umaru Musa Yar'Adua:** President from 2007 until his death in 2010.
- **Goodluck Jonathan:** Vice President who became President (2010–2015).
- **Bola Ahmed Tinubu:** Elected President in 2023.

Nigeria's political journey reflects a complex interplay of military and civilian rule, regional dynamics, and the ongoing quest for democratic consolidation and national development.
""",



    # Consolidated National Anthem - Using Markdown list for proper display
    "National Anthem of Nigeria": """
    Nigeria currently uses "Nigeria, We Hail Thee" as its national anthem, readopted on May 29, 2024.

    * **Verse 1:**
      Nigeria, we hail thee,
      Our own dear native land,
      Though tribe and tongue may differ,
      In brotherhood, we stand,
      Nigerians all, and proud to serve
      Our sovereign Motherland.

    * **Verse 2:**
      Our flag shall be a symbol
      That truth and justice reign,
      In peace or battle honour'd,
      And this we count as gain,
      To hand on to our children
      A banner without stain.

    * **Verse 3:**
      O God of all creation,
      Grant this our one request,
      Help us to build a nation
      Where no man is oppressed,
      And so with peace and plenty,
      Nigeria may be blessed.
    """,

    # Current Governors of Nigerian States (as of May 2025) - Individual Entries
    "Governor of Abia State": "The current Governor of Abia State is Alex Otti (Labour Party).",
    "Abia State Governor": "The current Governor of Abia State is Alex Otti (Labour Party).",
    "Governor of Adamawa State": "The current Governor of Adamawa State is Ahmadu Umaru Fintiri (PDP).",
    "Adamawa State Governor": "The current Governor of Adamawa State is Ahmadu Umaru Fintiri (PDP).",
    "Governor of Akwa Ibom State": "The current Governor of Akwa Ibom State is Umo Eno (PDP).",
    "Akwa Ibom State Governor": "The current Governor of Akwa Ibom State is Umo Eno (PDP).",
    "Governor of Anambra State": "The current Governor of Anambra State is Charles Soludo (APGA).",
    "Anambra State Governor": "The current Governor of Anambra State is Charles Soludo (APGA).",
    "Governor of Bauchi State": "The current Governor of Bauchi State is Bala Muhammed (PDP).",
    "Bauchi State Governor": "The current Governor of Bauchi State is Bala Muhammed (PDP).",
    "Governor of Bayelsa State": "The current Governor of Bayelsa State is Douye Diri (PDP).",
    "Bayelsa State Governor": "The current Governor of Bayelsa State is Douye Diri (PDP).",
    "Governor of Benue State": "The current Governor of Benue State is Hyacinth Alia (APC).",
    "Benue State Governor": "The current Governor of Benue State is Hyacinth Alia (APC).",
    "Governor of Borno State": "The current Governor of Borno State is Babagana Zulum (APC).",
    "Borno State Governor": "The current Governor of Borno State is Babagana Zulum (APC).",
    "Governor of Cross River State": "The current Governor of Cross River State is Bassey Otu (APC).",
    "Cross River State Governor": "The current Governor of Cross River State is Bassey Otu (APC).",
    "Governor of Delta State": "The current Governor of Delta State is Sheriff Oborevwori (APC).",
    "Delta State Governor": "The current Governor of Delta State is Sheriff Oborevwori (APC).",
    "Governor of Ebonyi State": "The current Governor of Ebonyi State is Francis Nwifuru (APC).",
    "Ebonyi State Governor": "The current Governor of Ebonyi State is Francis Nwifuru (APC).",
    "Governor of Edo State": "The current Governor of Edo State is Monday Okpebholo (APC).",
    "Edo State Governor": "The current Governor of Edo State is Monday Okpebholo (APC).",
    "Governor of Ekiti State": "The current Governor of Ekiti State is Biodun Oyebanji (APC).",
    "Ekiti State Governor": "The current Governor of Ekiti State is Biodun Oyebanji (APC).",
    "Governor of Enugu State": "The current Governor of Enugu State is Peter Mbah (PDP).",
    "Enugu State Governor": "The current Governor of Enugu State is Peter Mbah (PDP).",
    "Governor of Gombe State": "The current Governor of Gombe State is Muhammad Inuwa Yahaya (APC).",
    "Gombe State Governor": "The current Governor of Gombe State is Muhammad Inuwa Yahaya (APC).",
    "Governor of Imo State": "The current Governor of Imo State is Hope Uzodinma (APC).",
    "Imo State Governor": "The current Governor of Imo State is Hope Uzodinma (APC).",
    "Governor of Jigawa State": "The current Governor of Jigawa State is Umar Namadi (APC).",
    "Jigawa State Governor": "The current Governor of Jigawa State is Umar Namadi (APC).",
    "Governor of Kaduna State": "The current Governor of Kaduna State is Uba Sani (APC).",
    "Kaduna State Governor": "The current Governor of Kaduna State is Uba Sani (APC).",
    "Governor of Kano State": "The current Governor of Kano State is Abba Kabir Yusuf (New Nigeria Peoples Party - NNPP).",
    "Kano State Governor": "The current Governor of Kano State is Abba Kabir Yusuf (New Nigeria Peoples Party - NNPP).",
    "Governor of Katsina State": "The current Governor of Katsina State is Dikko Umaru Radda (APC).",
    "Katsina State Governor": "The current Governor of Katsina State is Dikko Umaru Radda (APC).",
    "Governor of Kebbi State": "The current Governor of Kebbi State is Nasir Idris (APC).",
    "Kebbi State Governor": "The current Governor of Kebbi State is Nasir Idris (APC).",
    "Governor of Kogi State": "The current Governor of Kogi State is Ahmed Usman Ododo (APC).",
    "Kogi State Governor": "The current Governor of Kogi State is Ahmed Usman Ododo (APC).",
    "Governor of Kwara State": "The current Governor of Kwara State is AbdulRahman AbdulRazaq (APC).",
    "Kwara State Governor": "The current Governor of Kwara State is AbdulRahman AbdulRazaq (APC).",
    "Governor of Lagos State": "The current Governor of Lagos State is Babajide Sanwo-Olu (APC).",
    "Lagos State Governor": "The current Governor of Lagos State is Babajide Sanwo-Olu (APC).",
    "Governor of Nasarawa State": "The current Governor of Nasarawa State is Abdullahi Sule (APC).",
    "Nasarawa State Governor": "The current Governor of Nasarawa State is Abdullahi Sule (APC).",
    "Governor of Niger State": "The current Governor of Niger State is Mohammed Umar Bago (APC).",
    "Niger State Governor": "The current Governor of Niger State is Mohammed Umar Bago (APC).",
    "Governor of Ogun State": "The current Governor of Ogun State is Dapo Abiodun (APC).",
    "Ogun State Governor": "The current Governor of Ogun State is Dapo Abiodun (APC).",
    "Governor of Ondo State": "The current Governor of Ondo State is Lucky Aiyedatiwa (APC).",
    "Ondo State Governor": "The current Governor of Ondo State is Lucky Aiyedatiwa (APC).",
    "Governor of Osun State": "The current Governor of Osun State is Ademola Adeleke (PDP).",
    "Osun State Governor": "The current Governor of Osun State is Ademola Adeleke (PDP).",
    "Governor of Oyo State": "The current Governor of Oyo State is Seyi Makinde (PDP).",
    "Oyo State Governor": "The current Governor of Oyo State is Seyi Makinde (PDP).",
    "Governor of Plateau State": "The current Governor of Plateau State is Caleb Mutfwang (PDP).",
    "Plateau State Governor": "The current Governor of Plateau State is Caleb Mutfwang (PDP).",
    "Governor of Rivers State": "The current Governor of Rivers State is Siminalayi Fubara (PDP).",
    "Rivers State Governor": "The current Governor of Rivers State is Siminalayi Fubara (PDP).",
    "Governor of Sokoto State": "The current Governor of Sokoto State is Ahmad Aliyu (APC).",
    "Sokoto State Governor": "The current Governor of Sokoto State is Ahmad Aliyu (APC).",
    "Governor of Taraba State": "The current Governor of Taraba State is Agbu Kefas (PDP).",
    "Taraba State Governor": "The current Governor of Taraba State is Agbu Kefas (PDP).",
    "Governor of Yobe State": "The current Governor of Yobe State is Mai Mala Buni (APC).",
    "Yobe State Governor": "The current Governor of Yobe State is Mai Mala Buni (APC).",
    "Governor of Zamfara State": "The current Governor of Zamfara State is Dauda Lawal (PDP).",
    "Zamfara State Governor": "The current Governor of Zamfara State is Dauda Lawal (PDP).",
    "FCT Minister": "The current Minister of the Federal Capital Territory (FCT) is Nyesom Wike (APC).",
    "Federal Capital Territory Minister": "The current Minister of the Federal Capital Territory (FCT) is Nyesom Wike (APC). Note: The FCT is administered by a Minister, not a Governor.",

   # Achievements in Nigeria's Education Sector (Consolidated into a single, comprehensive entry)
    "Achievements in Nigeria's Education Sector summary": "Nigeria's education sector has seen significant efforts and achievements aimed at expanding access, improving quality, and integrating technology.",
    "Education sector achievements Nigeria": """
    A major recent achievement (reported in early 2025) is the successful reintegration of over four million out-of-school children into educational institutions within a single year. This was achieved through strategic policies like the DOTS framework (Data Repository, Out-of-School Education, Teacher Training and Development, and Skills Acquisition), with ongoing plans to enroll millions more annually. [Source: URNI Post, May 2025](https://unveilingnigeria.ng/post/nigeria-achieves-milestone-education-4-million-out-school-children-back-class)

    School enrollment has surged significantly from 30 million to 55 million learners, demonstrating increased access to basic and tertiary education, including a notable increase in enrollment for learners with disabilities (200,500 learners). [Source: URNI Post, May 2025](https://unveilingnigeria.ng/post/nigeria-achieves-milestone-education-4-million-out-school-children-back-class)

    The National Education Loan Fund (NELFUND) has been established to provide financial support to students, with 3 billion naira disbursed as of early 2025, easing the financial burden on students and their families. [Source: URNI Post, May 2025](https://unveilingnigeria.ng/post/nigeria-achieves-milestone-education-4-million-out-school-children-back-class)

    More than 85,662 teaching and non-teaching staff have received training, aiming to improve pedagogical methods and overall educational delivery. [Source: URNI Post, May 2025](https://unveilingnigeria.ng/post/nigeria-achieves-milestone-education-4-million-out-school-children-back-class)

    In terms of infrastructure, the Universal Basic Education Commission (UBEC) has provided over 40,000 new facilities for basic and senior secondary education, and the Tertiary Education Trust Fund (TETFUND) has contributed more than 6,500 facilities to higher education institutions, enhancing learning environments. [Source: URNI Post, May 2025](https://unveilingnigeria.ng/post/nigeria-achieves-milestone-education-4-million-out-school-children-back-class)

    Historically, Nigeria has seen the establishment of numerous federal and state universities, significantly expanding higher education access, with notable examples including the University of Nigeria, Nsukka (1960), Obafemi Awolowo University, Ile-Ife (1962), Ahmadu Bello University, Zaria (1962), and specialized Universities of Technology and Agriculture to focus on technical and vocational skills. [Source: Excellence and Education Network](https://exced.ucoz.com/index/legends_in_nigerian_education/0-162)

    The introduction of Transnational Education (TNE) is opening doors for Nigerian scholars to access world-class education at reduced costs and attracting foreign investments into the sector. [Source: URNI Post, May 2025](https://unveilingnigeria.ng/post/nigeria-achieves-milestone-education-4-million-out-school-children-back-class)

    Artificial intelligence and other technological innovations are being adopted to enhance teaching and learning processes, pushing for a more digitally-driven education system. [Source: URNI Post, May 2025](https://unveilingnigeria.ng/post/nigeria-achieves-milestone-education-4-million-out-school-children-back-class)

    Furthermore, enrollment quotas for medical schools, nursing schools, and other health professional training institutions have significantly increased from 28,000 to 64,000 annually to address the health workforce shortage. [Source: FMOHSW Ministerial Briefing, May 2024](https://fmino.gov.ng/achievements-in-the-health-sector-presentation-by-the-hon-cmhsw-muhammad-ali-pate-con-at-the-ministerial-sectoral-briefing-radio-house-abuja-may-24-2024/)
    """,
    "Education achievement highlights": """
    A major recent achievement (reported in early 2025) is the successful reintegration of over four million out-of-school children into educational institutions within a single year. This was achieved through strategic policies like the DOTS framework (Data Repository, Out-of-School Education, Teacher Training and Development, and Skills Acquisition), with ongoing plans to enroll millions more annually. [Source: URNI Post, May 2025](https://unveilingnigeria.ng/post/nigeria-achieves-milestone-education-4-million-out-school-children-back-class)

    School enrollment has surged significantly from 30 million to 55 million learners, demonstrating increased access to basic and tertiary education, including a notable increase in enrollment for learners with disabilities (200,500 learners). [Source: URNI Post, May 2025](https://unveilingnigeria.ng/post/nigeria-achieves-milestone-education-4-million-out-school-children-back-class)

    The National Education Loan Fund (NELFUND) has been established to provide financial support to students, with 3 billion naira disbursed as of early 2025, easing the financial burden on students and their families. [Source: URNI Post, May 2025](https://unveilingnigeria.ng/post/nigeria-achieves-milestone-education-4-million-out-school-children-back-class)

    More than 85,662 teaching and non-teaching staff have received training, aiming to improve pedagogical methods and overall educational delivery. [Source: URNI Post, May 2025](https://unveilingnigeria.ng/post/nigeria-achieves-milestone-education-4-million-out-school-children-back-class)

    In terms of infrastructure, the Universal Basic Education Commission (UBEC) has provided over 40,000 new facilities for basic and senior secondary education, and the Tertiary Education Trust Fund (TETFUND) has contributed more than 6,500 facilities to higher education institutions, enhancing learning environments. [Source: URNI Post, May 2025](https://unveilingnigeria.ng/post/nigeria-achieves-milestone-education-4-million-out-school-children-back-class)

    Historically, Nigeria has seen the establishment of numerous federal and state universities, significantly expanding higher education access, with notable examples including the University of Nigeria, Nsukka (1960), Obafemi Awolowo University, Ile-Ife (1962), Ahmadu Bello University, Zaria (1962), and specialized Universities of Technology and Agriculture to focus on technical and vocational skills. [Source: Excellence and Education Network](https://exced.ucoz.com/index/legends_in_nigerian_education/0-162)

    The introduction of Transnational Education (TNE) is opening doors for Nigerian scholars to access world-class education at reduced costs and attracting foreign investments into the sector. [Source: URNI Post, May 2025](https://unveilingnigeria.ng/post/nigeria-achieves-milestone-education-4-million-out-school-children-back-class)

    Artificial intelligence and other technological innovations are being adopted to enhance teaching and learning processes, pushing for a more digitally-driven education system. [Source: URNI Post, May 2025](https://unveilingnigeria.ng/post/nigeria-achieves-milestone-education-4-million-out-school-children-back-class)

    Furthermore, enrollment quotas for medical schools, nursing schools, and other health professional training institutions have significantly increased from 28,000 to 64,000 annually to address the health workforce shortage. [Source: FMOHSW Ministerial Briefing, May 2024](https://fmino.gov.ng/achievements-in-the-health-sector-presentation-by-the-hon-cmhsw-muhammad-ali-pate-con-at-the-ministerial-sectoral-briefing-radio-house-abuja-may-24-2024/)
    """,
    "Education progress Nigeria": """
    A major recent achievement (reported in early 2025) is the successful reintegration of over four million out-of-school children into educational institutions within a single year. This was achieved through strategic policies like the DOTS framework (Data Repository, Out-of-School Education, Teacher Training and Development, and Skills Acquisition), with ongoing plans to enroll millions more annually. [Source: URNI Post, May 2025](https://unveilingnigeria.ng/post/nigeria-achieves-milestone-education-4-million-out-school-children-back-class)

    School enrollment has surged significantly from 30 million to 55 million learners, demonstrating increased access to basic and tertiary education, including a notable increase in enrollment for learners with disabilities (200,500 learners). [Source: URNI Post, May 2025](https://unveilingnigeria.ng/post/nigeria-achieves-milestone-education-4-million-out-school-children-back-class)

    The National Education Loan Fund (NELFUND) has been established to provide financial support to students, with 3 billion naira disbursed as of early 2025, easing the financial burden on students and their families. [Source: URNI Post, May 2025](https://unveilingnigeria.ng/post/nigeria-achieves-milestone-education-4-million-out-school-children-back-class)

    More than 85,662 teaching and non-teaching staff have received training, aiming to improve pedagogical methods and overall educational delivery. [Source: URNI Post, May 2025](https://unveilingnigeria.ng/post/nigeria-achieves-milestone-education-4-million-out-school-children-back-class)

    In terms of infrastructure, the Universal Basic Education Commission (UBEC) has provided over 40,000 new facilities for basic and senior secondary education, and the Tertiary Education Trust Fund (TETFUND) has contributed more than 6,500 facilities to higher education institutions, enhancing learning environments. [Source: URNI Post, May 2025](https://unveilingnigeria.ng/post/nigeria-achieves-milestone-education-4-million-out-school-children-back-class)

    Historically, Nigeria has seen the establishment of numerous federal and state universities, significantly expanding higher education access, with notable examples including the University of Nigeria, Nsukka (1960), Obafemi Awolowo University, Ile-Ife (1962), Ahmadu Bello University, Zaria (1962), and specialized Universities of Technology and Agriculture to focus on technical and vocational skills. [Source: Excellence and Education Network](https://exced.ucoz.com/index/legends_in_nigerian_education/0-162)

    The introduction of Transnational Education (TNE) is opening doors for Nigerian scholars to access world-class education at reduced costs and attracting foreign investments into the sector. [Source: URNI Post, May 2025](https://unveilingnigeria.ng/post/nigeria-achieves-milestone-education-4-million-out-school-children-back-class)

    Artificial intelligence and other technological innovations are being adopted to enhance teaching and learning processes, pushing for a more digitally-driven education system. [Source: URNI Post, May 2025](https://unveilingnigeria.ng/post/nigeria-achieves-milestone-education-4-million-out-school-children-back-class)

    Furthermore, enrollment quotas for medical schools, nursing schools, and other health professional training institutions have significantly increased from 28,000 to 64,000 annually to address the health workforce shortage. [Source: FMOHSW Ministerial Briefing, May 2024](https://fmino.gov.ng/achievements-in-the-health-sector-presentation-by-the-hon-cmhsw-muhammad-ali-pate-con-at-the-ministerial-sectoral-briefing-radio-house-abuja-may-24-2024/)
    """,

    # Achievements in Nigeria's Agriculture Sector (Consolidated into a single, comprehensive entry)
    "Achievements in Nigeria's Agriculture Sector summary": "Agriculture remains a cornerstone of the Nigerian economy, with various policies and initiatives aimed at boosting food security, creating jobs, and increasing exports.",
    "Agriculture sector achievements Nigeria": """
    Agriculture remains a cornerstone of the Nigerian economy, contributing about 19.63% of the Gross Domestic Product (GDP) in 2023 and accounting for over 35% of total employment, providing livelihoods for most Nigerians. [Source: VON, Oct 2024](https://von.gov.ng/driving-nigerias-agricultural-productivity-through-policies-programmes-and-projects-since-1960/)

    Nigeria is a leading global producer of several key crops (2022 data), including being the world's largest producer of Cassava (59.6 million tons), Yam (47.5 million tons), Taro (3.3 million tons), Cowpea (2.6 million tons), and Sorghum (6.8 million tons). It is also a significant producer of okra (2nd), peanut (3rd), sweet potato (3rd), ginger (3rd), millet (4th), palm oil (4th), sesame seed (4th), and cocoa (4th). [Source: Wikipedia - Agriculture in Nigeria](https://en.wikipedia.org/wiki/Agriculture_in_Nigeria)

    While specific recent export revenue figures for the entire sector are dynamic, efforts are geared towards increasing agro-produce exports. For instance, Lagos State is actively encouraging and supporting agripreneurs to export produce, with an overall strategy to drive agricultural growth for food security, self-sufficiency, and exports to Africa and the world. [Source: NAN News, May 2025](https://nannews.ng/2025/05/23/lagos-lists-achievements-in-agriculture-woos-young-agriprenuers-through-agrinnovation/)

    Policy reforms and programmes have been instrumental in the sector's development, including the National Accelerated Food Production Programme (NAFPP, 1973), Operation Feed the Nation (OFN, 1976), the Agricultural Transformation Agenda Support Programme (2011), the Agricultural Promotion Policy (APP) / Green Alternative (2016-2020) which focused on rice production through initiatives like the Anchor Borrowers' Programme, and the ongoing National Agricultural Growth Scheme – Agro-Pocket (NAGS-AP) to stimulate productivity and yields. [Source: VON, Oct 2024](https://von.gov.ng/driving-nigerias-agricultural-productivity-through-policies-programmes-and-projects-since-1960/)

    Private sector engagement and agrinnovation initiatives are also crucial, with examples like Lagos State's "Agrinnovation Club" and "Lagos Agrithon," which provide grants (e.g., over N100 million to 26 businesses in 2024) and foster collaboration to modernize food systems and attract youth to agriculture. [Source: NAN News, May 2025](https://nannews.ng/2025/05/23/lagos-lists-achievements-in-agriculture-woos-young-agriprenuers-through-agrinnovation/)

    Livestock production occupies a central position with significant numbers of poultry (over 80 million), goats (76 million), sheep (43.4 million), cattle (18.4 million), and pigs (7.5 million) as of 2017 data. [Source: Wikipedia - Agriculture in Nigeria](https://en.wikipedia.org/wiki/Agriculture_in_Nigeria)
    """,
    "Agriculture achievement highlights": """
    Agriculture remains a cornerstone of the Nigerian economy, contributing about 19.63% of the Gross Domestic Product (GDP) in 2023 and accounting for over 35% of total employment, providing livelihoods for most Nigerians. [Source: VON, Oct 2024](https://von.gov.ng/driving-nigerias-agricultural-productivity-through-policies-programmes-and-projects-since-1960/)

    Nigeria is a leading global producer of several key crops (2022 data), including being the world's largest producer of Cassava (59.6 million tons), Yam (47.5 million tons), Taro (3.3 million tons), Cowpea (2.6 million tons), and Sorghum (6.8 million tons). It is also a significant producer of okra (2nd), peanut (3rd), sweet potato (3rd), ginger (3rd), millet (4th), palm oil (4th), sesame seed (4th), and cocoa (4th). [Source: Wikipedia - Agriculture in Nigeria](https://en.wikipedia.org/wiki/Agriculture_in_Nigeria)

    While specific recent export revenue figures for the entire sector are dynamic, efforts are geared towards increasing agro-produce exports. For instance, Lagos State is actively encouraging and supporting agripreneurs to export produce, with an overall strategy to drive agricultural growth for food security, self-sufficiency, and exports to Africa and the world. [Source: NAN News, May 2025](https://nannews.ng/2025/05/23/lagos-lists-achievements-in-agriculture-woos-young-agriprenuers-through-agrinnovation/)

    Policy reforms and programmes have been instrumental in the sector's development, including the National Accelerated Food Production Programme (NAFPP, 1973), Operation Feed the Nation (OFN, 1976), the Agricultural Transformation Agenda Support Programme (2011), the Agricultural Promotion Policy (APP) / Green Alternative (2016-2020) which focused on rice production through initiatives like the Anchor Borrowers' Programme, and the ongoing National Agricultural Growth Scheme – Agro-Pocket (NAGS-AP) to stimulate productivity and yields. [Source: VON, Oct 2024](https://von.gov.ng/driving-nigerias-agricultural-productivity-through-policies-programmes-and-projects-since-1960/)

    Private sector engagement and agrinnovation initiatives are also crucial, with examples like Lagos State's "Agrinnovation Club" and "Lagos Agrithon," which provide grants (e.g., over N100 million to 26 businesses in 2024) and foster collaboration to modernize food systems and attract youth to agriculture. [Source: NAN News, May 2025](https://nannews.ng/2025/05/23/lagos-lists-achievements-in-agriculture-woos-young-agriprenuers-through-agrinnovation/)

    Livestock production occupies a central position with significant numbers of poultry (over 80 million), goats (76 million), sheep (43.4 million), cattle (18.4 million), and pigs (7.5 million) as of 2017 data. [Source: Wikipedia - Agriculture in Nigeria](https://en.wikipedia.org/wiki/Agriculture_in_Nigeria)
    """,
    "Agricultural progress Nigeria": """
    Agriculture remains a cornerstone of the Nigerian economy, contributing about 19.63% of the Gross Domestic Product (GDP) in 2023 and accounting for over 35% of total employment, providing livelihoods for most Nigerians. [Source: VON, Oct 2024](https://von.gov.ng/driving-nigerias-agricultural-productivity-through-policies-programmes-and-projects-since-1960/)

    Nigeria is a leading global producer of several key crops (2022 data), including being the world's largest producer of Cassava (59.6 million tons), Yam (47.5 million tons), Taro (3.3 million tons), Cowpea (2.6 million tons), and Sorghum (6.8 million tons). It is also a significant producer of okra (2nd), peanut (3rd), sweet potato (3rd), ginger (3rd), millet (4th), palm oil (4th), sesame seed (4th), and cocoa (4th). [Source: Wikipedia - Agriculture in Nigeria](https://en.wikipedia.org/wiki/Agriculture_in_Nigeria)

    While specific recent export revenue figures for the entire sector are dynamic, efforts are geared towards increasing agro-produce exports. For instance, Lagos State is actively encouraging and supporting agripreneurs to export produce, with an overall strategy to drive agricultural growth for food security, self-sufficiency, and exports to Africa and the world. [Source: NAN News, May 2025](https://nannews.ng/2025/05/23/lagos-lists-achievements-in-agriculture-woos-young-agriprenuers-through-agrinnovation/)

    Policy reforms and programmes have been instrumental in the sector's development, including the National Accelerated Food Production Programme (NAFPP, 1973), Operation Feed the Nation (OFN, 1976), the Agricultural Transformation Agenda Support Programme (2011), the Agricultural Promotion Policy (APP) / Green Alternative (2016-2020) which focused on rice production through initiatives like the Anchor Borrowers' Programme, and the ongoing National Agricultural Growth Scheme – Agro-Pocket (NAGS-AP) to stimulate productivity and yields. [Source: VON, Oct 2024](https://von.gov.ng/driving-nigerias-agricultural-productivity-through-policies-programmes-and-projects-since-1960/)

    Private sector engagement and agrinnovation initiatives are also crucial, with examples like Lagos State's "Agrinnovation Club" and "Lagos Agrithon," which provide grants (e.g., over N100 million to 26 businesses in 2024) and foster collaboration to modernize food systems and attract youth to agriculture. [Source: NAN News, May 2025](https://nannews.ng/2025/05/23/lagos-lists-achievements-in-agriculture-woos-young-agriprenuers-through-agrinnovation/)

    Livestock production occupies a central position with significant numbers of poultry (over 80 million), goats (76 million), sheep (43.4 million), cattle (18.4 million), and pigs (7.5 million) as of 2017 data. [Source: Wikipedia - Agriculture in Nigeria](https://en.wikipedia.org/wiki/Agriculture_in_Nigeria)
    """,

    # Achievements in Nigeria's Agriculture Sector (Detailed List Format)
    "Agriculture achievement: Contribution to GDP and Employment": """
    Agriculture contributed about 19.63% of Nigeria's Gross Domestic Product (GDP) in 2023 and accounted for over 35% of total employment, providing livelihoods for most Nigerians.
    [Source: VON, Oct 2024](https://von.gov.ng/driving-nigerias-agricultural-productivity-through-policies-programmes-and-projects-since-1960/)
    """,
    "Agriculture achievement: Major Global Producer": """
    Nigeria is a leading global producer of several key crops (2022 data):
    * **Cassava:** World's largest producer (59.6 million tons).
    * **Yam:** World's largest producer (47.5 million tons).
    * **Taro:** World's largest producer (3.3 million tons).
    * **Cowpea:** World's largest producer (2.6 million tons).
    * **Sorghum:** World's largest producer (6.8 million tons).
    * Significant producer of okra (2nd), peanut (3rd), sweet potato (3rd), ginger (3rd), millet (4th), palm oil (4th), sesame seed (4th), and cocoa (4th).
    [Source: Wikipedia - Agriculture in Nigeria](https://en.wikipedia.org/wiki/Agriculture_in_Nigeria)
    """,
    "Agriculture achievement: Export Rate and Revenue initiatives": """
    While specific recent export revenue figures for the entire sector are dynamic, efforts are geared towards increasing agro-produce exports.
    For instance, Lagos State is actively encouraging and supporting agripreneurs to export produce.
    The overall strategy includes driving agricultural growth to contribute to food security, self-sufficiency, and exports to Africa and the world.
    [Source: NAN News, May 2025](https://nannews.ng/2025/05/23/lagos-lists-achievements-in-agriculture-woos-young-agriprenuers-through-agrinnovation/)
    """,
    "Agriculture achievement: Policy Reforms and Programmes": """
    * **National Accelerated Food Production Programme (NAFPP, 1973):** Encouraged increased food production through modern agricultural practices.
    * **Operation Feed the Nation (OFN, 1976):** Promoted individual and group food production, subsidized fertilizers, constructed storage facilities, and subsidized land preparation and agrochemicals. It significantly raised awareness of agriculture's role in food security.
    * **Agricultural Transformation Agenda Support Programme (2011):** Focused on revitalizing the sector, driving income growth, and achieving food and nutritional security.
    * **Agricultural Promotion Policy (APP) / Green Alternative (2016-2020):** Aimed at improving farmers' access to loans, upscaling production skills, and increasing acreage, with special investments in rice production (e.g., Anchor Borrowers' Programme).
    * **National Agricultural Growth Scheme – Agro-Pocket (NAGS-AP):** Designed to stimulate increased productivity and higher yields, ensuring a significant impact on food production under the current administration.
    [Source: VON, Oct 2024](https://von.gov.ng/driving-nigerias-agricultural-productivity-through-policies-programmes-and-projects-since-1960/)
    """,
    "Agriculture achievement: Private Sector Engagement and Agrinnovation": """
    Lagos State, for instance, has actively wooed young agripreneurs through initiatives like the "Agrinnovation Club" and "Lagos Agrithon," providing grants (e.g., over N100 million to 26 businesses in 2024) and fostering collaboration to modernize food systems and attract youth to agriculture.
    [Source: NAN News, May 2025](https://nannews.ng/2025/05/23/lagos-lists-achievements-in-agriculture-woos-young-agriprenuers-through-agrinnovation/)
    """,
    "Agriculture achievement: Livestock Production": """
    Livestock production occupies a central position with significant numbers of poultry (over 80 million), goats (76 million), sheep (43.4 million), cattle (18.4 million), and pigs (7.5 million) as of 2017 data.
    [Source: Wikipedia - Agriculture in Nigeria](https://en.wikipedia.org/wiki/Agriculture_in_Nigeria)
    """,
    # Achievements in Nigeria's Agriculture Sector (Detailed List Format)
    "Achievements in Nigeria's Agriculture Sector summary": "Agriculture remains a cornerstone of the Nigerian economy, with various policies and initiatives aimed at boosting food security, creating jobs, and increasing exports.",
    "Agriculture achievement: Contribution to GDP and Employment": """
    Agriculture contributed about 19.63% of Nigeria's Gross Domestic Product (GDP) in 2023 and accounted for over 35% of total employment, providing livelihoods for most Nigerians.
    [Source: VON, Oct 2024](https://von.gov.ng/driving-nigerias-agricultural-productivity-through-policies-programmes-and-projects-since-1960/)
    """,
    "Agriculture achievement: Major Global Producer": """
    Nigeria is a leading global producer of several key crops (2022 data):
    * **Cassava:** World's largest producer (59.6 million tons).
    * **Yam:** World's largest producer (47.5 million tons).
    * **Taro:** World's largest producer (3.3 million tons).
    * **Cowpea:** World's largest producer (2.6 million tons).
    * **Sorghum:** World's largest producer (6.8 million tons).
    * Significant producer of okra (2nd), peanut (3rd), sweet potato (3rd), ginger (3rd), millet (4th), palm oil (4th), sesame seed (4th), and cocoa (4th).
    [Source: Wikipedia - Agriculture in Nigeria](https://en.wikipedia.org/wiki/Agriculture_in_Nigeria)
    """,
    "Agriculture achievement: Export Rate and Revenue initiatives": """
    While specific recent export revenue figures for the entire sector are dynamic, efforts are geared towards increasing agro-produce exports.
    For instance, Lagos State is actively encouraging and supporting agripreneurs to export produce.
    The overall strategy includes driving agricultural growth to contribute to food security, self-sufficiency, and exports to Africa and the world.
    [Source: NAN News, May 2025](https://nannews.ng/2025/05/23/lagos-lists-achievements-in-agriculture-woos-young-agriprenuers-through-agrinnovation/)
    """,
    "Agriculture achievement: Policy Reforms and Programmes": """
    * **National Accelerated Food Production Programme (NAFPP, 1973):** Encouraged increased food production through modern agricultural practices.
    * **Operation Feed the Nation (OFN, 1976):** Promoted individual and group food production, subsidized fertilizers, constructed storage facilities, and subsidized land preparation and agrochemicals. It significantly raised awareness of agriculture's role in food security.
    * **Agricultural Transformation Agenda Support Programme (2011):** Focused on revitalizing the sector, driving income growth, and achieving food and nutritional security.
    * **Agricultural Promotion Policy (APP) / Green Alternative (2016-2020):** Aimed at improving farmers' access to loans, upscaling production skills, and increasing acreage, with special investments in rice production (e.g., Anchor Borrowers' Programme).
    * **National Agricultural Growth Scheme – Agro-Pocket (NAGS-AP):** Designed to stimulate increased productivity and higher yields, ensuring a significant impact on food production under the current administration.
    [Source: VON, Oct 2024](https://von.gov.ng/driving-nigerias-agricultural-productivity-through-policies-programmes-and-projects-since-1960/)
    """,
    "Agriculture achievement: Private Sector Engagement and Agrinnovation": """
    Lagos State, for instance, has actively wooed young agripreneurs through initiatives like the "Agrinnovation Club" and "Lagos Agrithon," providing grants (e.g., over N100 million to 26 businesses in 2024) and fostering collaboration to modernize food systems and attract youth to agriculture.
    [Source: NAN News, May 2025](https://nannews.ng/2025/05/23/lagos-lists-achievements-in-agriculture-woos-young-agriprenuers-through-agrinnovation/)
    """,
    "Agriculture achievement: Livestock Production": """
    Livestock production occupies a central position with significant numbers of poultry (over 80 million), goats (76 million), sheep (43.4 million), cattle (18.4 million), and pigs (7.5 million) as of 2017 data.
    [Source: Wikipedia - Agriculture in Nigeria](https://en.wikipedia.org/wiki/Agriculture_in_Nigeria)
    """

    # Achievements in Nigeria's Technology Sector (Consolidated)
    "Achievements in Nigeria's Technology Sector summary" "Nigeria's technology sector is rapidly growing, positioning the country as a significant player in Africa's digital economy, driven by mobile connectivity, innovation, and a vibrant startup ecosystem.",
    "Technology sector achievements Nigeria": """
    Nigeria's technology sector is rapidly growing, positioning the country as a significant player in Africa's digital economy, driven by mobile connectivity, innovation, and a vibrant startup ecosystem.

    The country has witnessed an unprecedented surge in digitalization, with mobile network access playing a pivotal role. This includes widespread adoption of 4G technology and the nation stepping into the 5G era, facilitated by government strategy to leverage digital technology for economic diversification. [Source: Ericsson Blog, Aug 2023](https://www.ericsson.com/en/blog/middle-east-africa/2023/unleashing-sustainable-digital-transformation-in-nigeria)

    Mobile money is playing a pivotal role in enhancing financial resilience, driving higher savings, and fostering financial inclusion for the unbanked. The Central Bank of Nigeria's introduction of Payment Service Bank (PSB) licenses has catalyzed massive growth in registered agents and expanded mobile financial services. Financial technologies like USSD, e-payment features, and two-factor authentication have made transactions infinitely safer and more secure. Nigeria's tech startups attracted $5.2 billion in venture capital in 2022, with West Africa (led by Nigeria) accounting for the largest share. [Source: Tony Elumelu Foundation, Apr 2023](https://www.tonyelumelufoundation.org/wp-content/uploads/dlm_uploads/2022/08/The-Future-of-Technology-and-Innovation-in-Nigeria.pdf)

    Nigeria is becoming the destination for Africa's promising tech startups. The country has seen the emergence of several "unicorns" (startups valued over $1 billion), particularly in the FinTech space (e.g., Flutterwave, Paystack, Interswitch). [Source: Tony Elumelu Foundation, Apr 2023](https://www.tonyelumelufoundation.org/wp-content/uploads/dlm_uploads/2022/08/The-Future-of-Technology-and-Innovation-in-Nigeria.pdf)

    Over 65% of Nigerian respondents in a recent Ericsson ConsumerLab study engage in remote work at least once a week, relying on mobile broadband solutions (3G/4G/5G routers or smartphone tethering) for home connectivity, indicating a profound transformation in the workplace. [Source: Ericsson Blog, Aug 2023](https://www.ericsson.com/en/blog/middle-east-africa/2023/unleashing-sustainable-digital-transformation-in-nigeria)

    Digital transformation is evident across public and private sectors. Banks have implemented Open Digital Banking platforms and paperless initiatives. For example, UBA's Leo chatbot became a digital persona for automated service across social media platforms. [Source: Tony Elumelu Foundation, Apr 2023](https://www.tonyelumelufoundation.org/wp-content/uploads/dlm_uploads/2022/08/The-Future-of-Technology-and-Innovation-in-Nigeria.pdf)

    Initiatives like the National Identification Number (NIN) and Bank Verification Number (BVN) leverage technology to formalize identity and expand financial services.
    """,
    "Technology achievement highlights": """
    Nigeria's technology sector is rapidly growing, positioning the country as a significant player in Africa's digital economy, driven by mobile connectivity, innovation, and a vibrant startup ecosystem.

    The country has witnessed an unprecedented surge in digitalization, with mobile network access playing a pivotal role. This includes widespread adoption of 4G technology and the nation stepping into the 5G era, facilitated by government strategy to leverage digital technology for economic diversification. [Source: Ericsson Blog, Aug 2023](https://www.ericsson.com/en/blog/middle-east-africa/2023/unleashing-sustainable-digital-transformation-in-nigeria)

    Mobile money is playing a pivotal role in enhancing financial resilience, driving higher savings, and fostering financial inclusion for the unbanked. The Central Bank of Nigeria's introduction of Payment Service Bank (PSB) licenses has catalyzed massive growth in registered agents and expanded mobile financial services. Financial technologies like USSD, e-payment features, and two-factor authentication have made transactions infinitely safer and more secure. Nigeria's tech startups attracted $5.2 billion in venture capital in 2022, with West Africa (led by Nigeria) accounting for the largest share. [Source: Tony Elumelu Foundation, Apr 2023](https://www.tonyelumelufoundation.org/wp-content/uploads/dlm_uploads/2022/08/The-Future-of-Technology-and-Innovation-in-Nigeria.pdf)

    Nigeria is becoming the destination for Africa's promising tech startups. The country has seen the emergence of several "unicorns" (startups valued over $1 billion), particularly in the FinTech space (e.g., Flutterwave, Paystack, Interswitch). [Source: Tony Elumelu Foundation, Apr 2023](https://www.tonyelumelufoundation.org/wp-content/uploads/dlm_uploads/2022/08/The-Future-of-Technology-and-Innovation-in-Nigeria.pdf)

    Over 65% of Nigerian respondents in a recent Ericsson ConsumerLab study engage in remote work at least once a week, relying on mobile broadband solutions (3G/4G/5G routers or smartphone tethering) for home connectivity, indicating a profound transformation in the workplace. [Source: Ericsson Blog, Aug 2023](https://www.ericsson.com/en/blog/middle-east-africa/2023/unleashing-sustainable-digital-transformation-in-nigeria)

    Digital transformation is evident across public and private sectors. Banks have implemented Open Digital Banking platforms and paperless initiatives. For example, UBA's Leo chatbot became a digital persona for automated service across social media platforms. [Source: Tony Elumelu Foundation, Apr 2023](https://www.tonyelumelufoundation.org/wp-content/uploads/dlm_uploads/2022/08/The-Future-of-Technology-and-Innovation-in-Nigeria.pdf)

    Initiatives like the National Identification Number (NIN) and Bank Verification Number (BVN) leverage technology to formalize identity and expand financial services.
    """,
    "Technological progress Nigeria": """
    Nigeria's technology sector is rapidly growing, positioning the country as a significant player in Africa's digital economy, driven by mobile connectivity, innovation, and a vibrant startup ecosystem.

    The country has witnessed an unprecedented surge in digitalization, with mobile network access playing a pivotal role. This includes widespread adoption of 4G technology and the nation stepping into the 5G era, facilitated by government strategy to leverage digital technology for economic diversification. [Source: Ericsson Blog, Aug 2023](https://www.ericsson.com/en/blog/middle-east-africa/2023/unleashing-sustainable-digital-transformation-in-nigeria)

    Mobile money is playing a pivotal role in enhancing financial resilience, driving higher savings, and fostering financial inclusion for the unbanked. The Central Bank of Nigeria's introduction of Payment Service Bank (PSB) licenses has catalyzed massive growth in registered agents and expanded mobile financial services. Financial technologies like USSD, e-payment features, and two-factor authentication have made transactions infinitely safer and more secure. Nigeria's tech startups attracted $5.2 billion in venture capital in 2022, with West Africa (led by Nigeria) accounting for the largest share. [Source: Tony Elumelu Foundation, Apr 2023](https://www.tonyelumelufoundation.org/wp-content/uploads/dlm_uploads/2022/08/The-Future-of-Technology-and-Innovation-in-Nigeria.pdf)

    Nigeria is becoming the destination for Africa's promising tech startups. The country has seen the emergence of several "unicorns" (startups valued over $1 billion), particularly in the FinTech space (e.g., Flutterwave, Paystack, Interswitch). [Source: Tony Elumelu Foundation, Apr 2023](https://www.tonyelumelufoundation.org/wp-content/uploads/dlm_uploads/2022/08/The-Future-of-Technology-and-Innovation-in-Nigeria.pdf)

    Over 65% of Nigerian respondents in a recent Ericsson ConsumerLab study engage in remote work at least once a week, relying on mobile broadband solutions (3G/4G/5G routers or smartphone tethering) for home connectivity, indicating a profound transformation in the workplace. [Source: Ericsson Blog, Aug 2023](https://www.ericsson.com/en/blog/middle-east-africa/2023/unleashing-sustainable-digital-transformation-in-nigeria)

    Digital transformation is evident across public and private sectors. Banks have implemented Open Digital Banking platforms and paperless initiatives. For example, UBA's Leo chatbot became a digital persona for automated service across social media platforms. [Source: Tony Elumelu Foundation, Apr 2023](https://www.tonyelumelufoundation.org/wp-content/uploads/dlm_uploads/2022/08/The-Future-of-Technology-and-Innovation-in-Nigeria.pdf)

    Initiatives like the National Identification Number (NIN) and Bank Verification Number (BVN) leverage technology to formalize identity and expand financial services.
    """,

    # Achievements in Nigeria's Health Sector (Consolidated)
    "Achievements in Nigeria's Health Sector summary": "Nigeria's health sector has seen significant reforms, increased investment, and targeted initiatives aimed at improving healthcare access, quality, and outcomes, particularly for vulnerable populations.",
    "Health sector achievements Nigeria": """
    Nigeria's health sector has seen significant reforms, increased investment, and targeted initiatives aimed at improving healthcare access, quality, and outcomes, particularly for vulnerable populations.

    A strategic blueprint, the Health Sector Renewal Investment Initiative, was launched by the Ministry of Health and Social Welfare (FMOHSW) to improve population health outcomes, particularly through primary healthcare and enhancing reproductive, maternal, and child health services. This includes a compact signed with all 36 states and the FCT. [Source: FMOHSW Ministerial Briefing, May 2024](https://fmino.gov.ng/achievements-in-the-health-sector-presentation-by-the-hon-cmhsw-muhammad-ali-pate-con-at-the-ministerial-sectoral-briefing-radio-house-abuja-may-24-2024/)

    Groundbreaking innovations like the Maternal and Newborn Mortality Reduction Initiative offer free caesarean sections to eligible Nigerian women, significantly reducing maternal and newborn mortality. [Source: Punch Newspapers, Jan 2025](https://punchng.com/a-stellar-year-for-nigerias-health-sector/)

    Over 53,000 frontline health workers have been retrained to deliver integrated, high-quality services. Plans are in place to equip at least 120,000 frontline health workers serving rural populations over the next three years. [Source: FMOHSW Ministerial Briefing, May 2024](https://fmino.gov.ng/achievements-in-the-health-sector-presentation-by-the-hon-cmhsw-muhammad-ali-pate-con-at-the-ministerial-sectoral-briefing-radio-house-abuja-may-24-2024/)

    The Basic Health Care Provision Fund (BHCPF) was redesigned and now covers approximately 10 million Nigerians, with a record 2.4 million citizens enrolling in the national health insurance scheme, enhancing access to affordable healthcare. [Source: Punch Newspapers, Jan 2025](https://punchng.com/a-stellar-year-for-nigerias-health-sector/)

    The sector has secured significant financing mechanisms, including a €1 billion European Investment Bank financing and a $1 billion Afreximbank financing to support incoming manufacturers in the health and life sciences sectors. Over 70 new healthcare manufacturing companies are in discussions, with 22 large-scale projects actively engaging international financiers. [Source: Punch Newspapers, Jan 2025](https://punchng.com/a-stellar-year-for-nigerias-health-sector/)

    The Presidential Unlocking Healthcare Value Chain Initiative aims to increase local manufacturing of rapid diagnostic tests (e.g., Abbott Diagnostics plant), medical oxygen (e.g., Global Gases group plant), essential antibiotics (e.g., Jawa Investments producing Amoxicillin-Clavulanic Acid locally), vaccines, and other health solutions. [Source: Punch Newspapers, Jan 2025](https://punchng.com/a-stellar-year-for-nigerias-health-sector/)

    Significant vaccination campaigns have been carried out: Over 5 million Nigerian children vaccinated against diphtheria; more than 10 million received tetanus and diphtheria vaccines; over 5 million received measles vaccines. Additionally, 4.95 million girls (9-14 years) in 15 states received HPV vaccines (80% target achieved in some areas), with plans for 6 million more. [Source: FMOHSW Ministerial Briefing, May 2024](https://fmino.gov.ng/achievements-in-the-health-sector-presentation-by-the-hon-cmhsw-muhammad-ali-pate-con-at-the-ministerial-sectoral-briefing-radio-house-abuja-may-24-2024/)

    Infrastructure improvements include federal hospitals successfully executing 201 specific infrastructure projects in the last year, and 179 specific pieces of important medical equipment procured and distributed across the six geopolitical zones. At least 1,400 Primary Health Care Centers are now equipped to provide skilled birth attendance. [Source: FMOHSW Ministerial Briefing, May 2024](https://fmino.gov.ng/achievements-in-the-health-sector-presentation-by-the-hon-cmhsw-muhammad-ali-pate-con-at-the-ministerial-sectoral-briefing-radio-house-abuja-may-24-2024/)

    Human resources for health recruitment has seen over 2,400 health workers (nurses, doctors, midwives) recruited to provide services. The intake capacity of medical and nursing schools has significantly increased from 28,000 to 64,000 annually. [Source: FMOHSW Ministerial Briefing, May 2024](https://fmino.gov.ng/achievements-in-the-health-sector-presentation-by-the-hon-cmhsw-muhammad-ali-pate-con-at-the-ministerial-sectoral-briefing-radio-house-abuja-may-24-2024/)
    """,
    "Health achievement highlights": """
    Nigeria's health sector has seen significant reforms, increased investment, and targeted initiatives aimed at improving healthcare access, quality, and outcomes, particularly for vulnerable populations.

    A strategic blueprint, the Health Sector Renewal Investment Initiative, was launched by the Ministry of Health and Social Welfare (FMOHSW) to improve population health outcomes, particularly through primary healthcare and enhancing reproductive, maternal, and child health services. This includes a compact signed with all 36 states and the FCT. [Source: FMOHSW Ministerial Briefing, May 2024](https://fmino.gov.ng/achievements-in-the-health-sector-presentation-by-the-hon-cmhsw-muhammad-ali-pate-con-at-the-ministerial-sectoral-briefing-radio-house-abuja-may-24-2024/)

    Groundbreaking innovations like the Maternal and Newborn Mortality Reduction Initiative offer free caesarean sections to eligible Nigerian women, significantly reducing maternal and newborn mortality. [Source: Punch Newspapers, Jan 2025](https://punchng.com/a-stellar-year-for-nigerias-health-sector/)

    Over 53,000 frontline health workers have been retrained to deliver integrated, high-quality services. Plans are in place to equip at least 120,000 frontline health workers serving rural populations over the next three years. [Source: FMOHSW Ministerial Briefing, May 2024](https://fmino.gov.ng/achievements-in-the-health-sector-presentation-by-the-hon-cmhsw-muhammad-ali-pate-con-at-the-ministerial-sectoral-briefing-radio-house-abuja-may-24-2024/)

    The Basic Health Care Provision Fund (BHCPF) was redesigned and now covers approximately 10 million Nigerians, with a record 2.4 million citizens enrolling in the national health insurance scheme, enhancing access to affordable healthcare. [Source: Punch Newspapers, Jan 2025](https://punchng.com/a-stellar-year-for-nigerias-health-sector/)

    The sector has secured significant financing mechanisms, including a €1 billion European Investment Bank financing and a $1 billion Afreximbank financing to support incoming manufacturers in the health and life sciences sectors. Over 70 new healthcare manufacturing companies are in discussions, with 22 large-scale projects actively engaging international financiers. [Source: Punch Newspapers, Jan 2025](https://punchng.com/a-stellar-year-for-nigerias-health-sector/)

    The Presidential Unlocking Healthcare Value Chain Initiative aims to increase local manufacturing of rapid diagnostic tests (e.g., Abbott Diagnostics plant), medical oxygen (e.g., Global Gases group plant), essential antibiotics (e.g., Jawa Investments producing Amoxicillin-Clavulanic Acid locally), vaccines, and other health solutions. [Source: Punch Newspapers, Jan 2025](https://punchng.com/a-stellar-year-for-nigerias-health-sector/)

    Significant vaccination campaigns have been carried out: Over 5 million Nigerian children vaccinated against diphtheria; more than 10 million received tetanus and diphtheria vaccines; over 5 million received measles vaccines. Additionally, 4.95 million girls (9-14 years) in 15 states received HPV vaccines (80% target achieved in some areas), with plans for 6 million more. [Source: FMOHSW Ministerial Briefing, May 2024](https://fmino.gov.ng/achievements-in-the-health-sector-presentation-by-the-hon-cmhsw-muhammad-ali-pate-con-at-the-ministerial-sectoral-briefing-radio-house-abuja-may-24-2024/)

    Infrastructure improvements include federal hospitals successfully executing 201 specific infrastructure projects in the last year, and 179 specific pieces of important medical equipment procured and distributed across the six geopolitical zones. At least 1,400 Primary Health Care Centers are now equipped to provide skilled birth attendance. [Source: FMOHSW Ministerial Briefing, May 2024](https://fmino.gov.ng/achievements-in-the-health-sector-presentation-by-the-hon-cmhsw-muhammad-ali-pate-con-at-the-ministerial-sectoral-briefing-radio-house-abuja-may-24-2024/)

    Human resources for health recruitment has seen over 2,400 health workers (nurses, doctors, midwives) recruited to provide services. The intake capacity of medical and nursing schools has significantly increased from 28,000 to 64,000 annually. [Source: FMOHSW Ministerial Briefing, May 2024](https://fmino.gov.ng/achievements-in-the-health-sector-presentation-by-the-hon-cmhsw-muhammad-ali-pate-con-at-the-ministerial-sectoral-briefing-radio-house-abuja-may-24-2024/)
    """,
    "Healthcare progress Nigeria": """
    Nigeria's health sector has seen significant reforms, increased investment, and targeted initiatives aimed at improving healthcare access, quality, and outcomes, particularly for vulnerable populations.

    A strategic blueprint, the Health Sector Renewal Investment Initiative, was launched by the Ministry of Health and Social Welfare (FMOHSW) to improve population health outcomes, particularly through primary healthcare and enhancing reproductive, maternal, and child health services. This includes a compact signed with all 36 states and the FCT. [Source: FMOHSW Ministerial Briefing, May 2024](https://fmino.gov.ng/achievements-in-the-health-sector-presentation-by-the-hon-cmhsw-muhammad-ali-pate-con-at-the-ministerial-sectoral-briefing-radio-house-abuja-may-24-2024/)

    Groundbreaking innovations like the Maternal and Newborn Mortality Reduction Initiative offer free caesarean sections to eligible Nigerian women, significantly reducing maternal and newborn mortality. [Source: Punch Newspapers, Jan 2025](https://punchng.com/a-stellar-year-for-nigerias-health-sector/)

    Over 53,000 frontline health workers have been retrained to deliver integrated, high-quality services. Plans are in place to equip at least 120,000 frontline health workers serving rural populations over the next three years. [Source: FMOHSW Ministerial Briefing, May 2024](https://fmino.gov.ng/achievements-in-the-health-sector-presentation-by-the-hon-cmhsw-muhammad-ali-pate-con-at-the-ministerial-sectoral-briefing-radio-house-abuja-may-24-2024/)

    The Basic Health Care Provision Fund (BHCPF) was redesigned and now covers approximately 10 million Nigerians, with a record 2.4 million citizens enrolling in the national health insurance scheme, enhancing access to affordable healthcare. [Source: Punch Newspapers, Jan 2025](https://punchng.com/a-stellar-year-for-nigerias-health-sector/)

    The sector has secured significant financing mechanisms, including a €1 billion European Investment Bank financing and a $1 billion Afreximbank financing to support incoming manufacturers in the health and life sciences sectors. Over 70 new healthcare manufacturing companies are in discussions, with 22 large-scale projects actively engaging international financiers. [Source: Punch Newspapers, Jan 2025](https://punchng.com/a-stellar-year-for-nigerias-health-sector/)

    The Presidential Unlocking Healthcare Value Chain Initiative aims to increase local manufacturing of rapid diagnostic tests (e.g., Abbott Diagnostics plant), medical oxygen (e.g., Global Gases group plant), essential antibiotics (e.g., Jawa Investments producing Amoxicillin-Clavulanic Acid locally), vaccines, and other health solutions. [Source: Punch Newspapers, Jan 2025](https://punchng.com/a-stellar-year-for-nigerias-health-sector/)

    Significant vaccination campaigns have been carried out: Over 5 million Nigerian children vaccinated against diphtheria; more than 10 million received tetanus and diphtheria vaccines; over 5 million received measles vaccines. Additionally, 4.95 million girls (9-14 years) in 15 states received HPV vaccines (80% target achieved in some areas), with plans for 6 million more. [Source: FMOHSW Ministerial Briefing, May 2024](https://fmino.gov.ng/achievements-in-the-health-sector-presentation-by-the-hon-cmhsw-muhammad-ali-pate-con-at-the-ministerial-sectoral-briefing-radio-house-abuja-may-24-2024/)

    Infrastructure improvements include federal hospitals successfully executing 201 specific infrastructure projects in the last year, and 179 specific pieces of important medical equipment procured and distributed across the six geopolitical zones. At least 1,400 Primary Health Care Centers are now equipped to provide skilled birth attendance. [Source: FMOHSW Ministerial Briefing, May 2024](https://fmino.gov.ng/achievements-in-the-health-sector-presentation-by-the-hon-cmhsw-muhammad-ali-pate-con-at-the-ministerial-sectoral-briefing-radio-house-abuja-may-24-2024/)

    Human resources for health recruitment has seen over 2,400 health workers (nurses, doctors, midwives) recruited to provide services. The intake capacity of medical and nursing schools has significantly increased from 28,000 to 64,000 annually. [Source: FMOHSW Ministerial Briefing, May 2024](https://fmino.gov.ng/achievements-in-the-health-sector-presentation-by-the-hon-cmhsw-muhammad-ali-pate-con-at-the-ministerial-sectoral-briefing-radio-house-abuja-may-24-2024/)
    """,

    # Achievements in Nigeria's Infrastructure Sector (Consolidated)
    "Achievements in Nigeria's Infrastructure Sector summary": "Nigeria has been actively pursuing ambitious infrastructure projects to improve connectivity, drive economic growth, and strengthen long-term development, despite facing significant deficits.",
    "Infrastructure sector achievements Nigeria": """
    Nigeria has been actively pursuing ambitious infrastructure projects to improve connectivity, drive economic growth, and strengthen long-term development, despite facing significant deficits.

    Major construction projects have improved transportation networks across the country, easing congestion and boosting trade. Significant progress has been noted in road and highway expansion in 2024, improving connectivity across urban and rural areas. [Source: The Estero, Feb 2025](https://www.olaniwunajayi.net/blog/nigerias-infrastructure-growth-in-2024-key-developments-and-2025-outlook/)

    Expanded rail lines now connect key cities, reducing travel time and supporting economic activity. The government's commitment to modernizing transport networks aligns with long-term economic development goals. [Source: The Estero, Feb 2025](https://www.olaniwunajayi.net/blog/nigerias-infrastructure-growth-in-2024-key-developments-and-2025-outlook/)

    Renovation and expansion of international airports (e.g., Lagos, Abuja, Kano, Port Harcourt) with new terminals, aiming to improve passenger experience and cargo handling.

    Efforts to modernize seaports to enhance efficiency, reduce congestion, and boost trade facilitation, including ongoing deep seaport projects like the Lekki Deep Seaport, which is expected to significantly boost cargo handling capacity.

    Ongoing efforts to improve electricity generation, transmission, and distribution, with investments in new power plants and efforts to improve grid stability. The Presidential Power Initiative (PPI) aims to upgrade the national grid.

    Investments in sustainable housing initiatives and smart city projects are reshaping Nigeria's urban landscape, with a focus on affordable housing. Developers are leveraging innovative construction methods to reduce costs and improve efficiency. [Source: The Estero, Feb 2025](https://www.olaniwunajayi.net/blog/nigerias-infrastructure-growth-in-2024-key-developments-and-2025-outlook/)

    Rapid growth in broadband penetration and the rollout of 5G technology in major cities have strengthened connectivity and accelerated digital transformation. Improved broadband penetration and government-backed digital inclusion initiatives are strengthening Nigeria's position as a key player in Africa's digital economy. [Source: The Estero, Feb 2025](https://www.olaniwunajayi.net/blog/nigerias-infrastructure-growth-in-2024-key-developments-and-2025-outlook/)

    The government is strengthening Public-Private Partnership (PPP) frameworks to attract private investment and ensure sustainable project financing across various infrastructure sectors. Reforms in construction regulations and land acquisition laws are part of this effort, making large-scale developments more feasible. [Source: The Estero, Feb 2025](https://www.olaniwunajayi.net/blog/nigerias-infrastructure-growth-in-2024-key-developments-and-2025-outlook/)

    Commitment to completing and reviving previously stalled infrastructure projects, demonstrating dedication to continuity in development.

    Construction of major bridges and flyovers in urban centers (e.g., Lagos) to ease traffic congestion and improve urban mobility.
    """,
    "Infrastructure achievement highlights": """
    Nigeria has been actively pursuing ambitious infrastructure projects to improve connectivity, drive economic growth, and strengthen long-term development, despite facing significant deficits.

    Major construction projects have improved transportation networks across the country, easing congestion and boosting trade. Significant progress has been noted in road and highway expansion in 2024, improving connectivity across urban and rural areas. [Source: The Estero, Feb 2025](https://www.olaniwunajayi.net/blog/nigerias-infrastructure-growth-in-2024-key-developments-and-2025-outlook/)

    Expanded rail lines now connect key cities, reducing travel time and supporting economic activity. The government's commitment to modernizing transport networks aligns with long-term economic development goals. [Source: The Estero, Feb 2025](https://www.olaniwunajayi.net/blog/nigerias-infrastructure-growth-in-2024-key-developments-and-2025-outlook/)

    Renovation and expansion of international airports (e.g., Lagos, Abuja, Kano, Port Harcourt) with new terminals, aiming to improve passenger experience and cargo handling.

    Efforts to modernize seaports to enhance efficiency, reduce congestion, and boost trade facilitation, including ongoing deep seaport projects like the Lekki Deep Seaport, which is expected to significantly boost cargo handling capacity.

    Ongoing efforts to improve electricity generation, transmission, and distribution, with investments in new power plants and efforts to improve grid stability. The Presidential Power Initiative (PPI) aims to upgrade the national grid.

    Investments in sustainable housing initiatives and smart city projects are reshaping Nigeria's urban landscape, with a focus on affordable housing. Developers are leveraging innovative construction methods to reduce costs and improve efficiency. [Source: The Estero, Feb 2025](https://www.olaniwunajayi.net/blog/nigerias-infrastructure-growth-in-2024-key-developments-and-2025-outlook/)

    Rapid growth in broadband penetration and the rollout of 5G technology in major cities have strengthened connectivity and accelerated digital transformation. Improved broadband penetration and government-backed digital inclusion initiatives are strengthening Nigeria's position as a key player in Africa's digital economy. [Source: The Estero, Feb 2025](https://www.olaniwunajayi.net/blog/nigerias-infrastructure-growth-in-2024-key-developments-and-2025-outlook/)

    The government is strengthening Public-Private Partnership (PPP) frameworks to attract private investment and ensure sustainable project financing across various infrastructure sectors. Reforms in construction regulations and land acquisition laws are part of this effort, making large-scale developments more feasible. [Source: The Estero, Feb 2025](https://www.olaniwunajayi.net/blog/nigerias-infrastructure-growth-in-2024-key-developments-and-2025-outlook/)

    Commitment to completing and reviving previously stalled infrastructure projects, demonstrating dedication to continuity in development.

    Construction of major bridges and flyovers in urban centers (e.g., Lagos) to ease traffic congestion and improve urban mobility.
    """,
    "Infrastructure development Nigeria": """
    Nigeria has been actively pursuing ambitious infrastructure projects to improve connectivity, drive economic growth, and strengthen long-term development, despite facing significant deficits.

    Major construction projects have improved transportation networks across the country, easing congestion and boosting trade. Significant progress has been noted in road and highway expansion in 2024, improving connectivity across urban and rural areas. [Source: The Estero, Feb 2025](https://www.olaniwunajayi.net/blog/nigerias-infrastructure-growth-in-2024-key-developments-and-2025-outlook/)

    Expanded rail lines now connect key cities, reducing travel time and supporting economic activity. The government's commitment to modernizing transport networks aligns with long-term economic development goals. [Source: The Estero, Feb 2025](https://www.olaniwunajayi.net/blog/nigerias-infrastructure-growth-in-2024-key-developments-and-2025-outlook/)

    Renovation and expansion of international airports (e.g., Lagos, Abuja, Kano, Port Harcourt) with new terminals, aiming to improve passenger experience and cargo handling.

    Efforts to modernize seaports to enhance efficiency, reduce congestion, and boost trade facilitation, including ongoing deep seaport projects like the Lekki Deep Seaport, which is expected to significantly boost cargo handling capacity.

    Ongoing efforts to improve electricity generation, transmission, and distribution, with investments in new power plants and efforts to improve grid stability. The Presidential Power Initiative (PPI) aims to upgrade the national grid.

    Investments in sustainable housing initiatives and smart city projects are reshaping Nigeria's urban landscape, with a focus on affordable housing. Developers are leveraging innovative construction methods to reduce costs and improve efficiency. [Source: The Estero, Feb 2025](https://www.olaniwunajayi.net/blog/nigerias-infrastructure-growth-in-2024-key-developments-and-2025-outlook/)

    Rapid growth in broadband penetration and the rollout of 5G technology in major cities have strengthened connectivity and accelerated digital transformation. Improved broadband penetration and government-backed digital inclusion initiatives are strengthening Nigeria's position as a key player in Africa's digital economy. [Source: The Estero, Feb 2025](https://www.olaniwunajayi.net/blog/nigerias-infrastructure-growth-in-2024-key-developments-and-2025-outlook/)

    The government is strengthening Public-Private Partnership (PPP) frameworks to attract private investment and ensure sustainable project financing across various infrastructure sectors. Reforms in construction regulations and land acquisition laws are part of this effort, making large-scale developments more feasible. [Source: The Estero, Feb 2025](https://www.olaniwunajayi.net/blog/nigerias-infrastructure-growth-in-2024-key-developments-and-2025-outlook/)

    Commitment to completing and reviving previously stalled infrastructure projects, demonstrating dedication to continuity in development.

    Construction of major bridges and flyovers in urban centers (e.g., Lagos) to ease traffic congestion and improve urban mobility.
    """,

    # Technology achievement: Mobile Connectivity and Digitalization
    "Technology achievement: Mobile Connectivity and Digitalization": """
    Nigeria has witnessed an unprecedented surge in digitalization, with mobile network access assuming a pivotal role.
    This includes widespread adoption of 4G technology and the nation stepping into the 5G era, facilitated by government strategy to leverage digital technology for economic diversification.
    [Source: Ericsson Blog, Aug 2023](https://www.ericsson.com/en/blog/middle-east-africa/2023/unleashing-sustainable-digital-transformation-in-nigeria)
    """,
    "Technology achievement: Growth of FinTech": """
    Mobile money is playing a pivotal role in enhancing financial resilience, driving higher savings, and fostering financial inclusion for the unbanked.
    The Central Bank of Nigeria's introduction of Payment Service Bank (PSB) licenses has catalyzed massive growth in registered agents and expanded mobile financial services.
    Financial technologies like USSD, e-payment features, and two-factor authentication have made transactions infinitely safer and more secure.
    Nigeria's tech startups attracted $5.2 billion in venture capital in 2022, with West Africa (led by Nigeria) accounting for the largest share.
    [Source: Tony Elumelu Foundation, Apr 2023](https://www.tonyelumelufoundation.org/wp-content/uploads/dlm_uploads/2022/08/The-Future-of-Technology-and-Innovation-in-Nigeria.pdf)
    """,
    "Technology achievement: Tech Startup Ecosystem": """
    Nigeria is becoming the destination for Africa's promising tech startups.
    The country has seen the emergence of several "unicorns" (startups valued over $1 billion), particularly in the FinTech space (e.g., Flutterwave, Paystack, Interswitch).
    [Source: Tony Elumelu Foundation, Apr 2023](https://www.tonyelumelufoundation.org/wp-content/uploads/dlm_uploads/2022/08/The-Future-of-Technology-and-Innovation-in-Nigeria.pdf)
    """,
    "Technology achievement: Remote and Hybrid Work Transformation": """
    Over 65% of Nigerian respondents in a recent Ericsson ConsumerLab study engage in remote work at least once a week, relying on mobile broadband solutions (3G/4G/5G routers or smartphone tethering) for home connectivity, indicating a profound transformation in the workplace.
    [Source: Ericsson Blog, Aug 2023](https://www.ericsson.com/en/blog/middle-east-africa/2023/unleashing-sustainable-digital-transformation-in-nigeria)
    """,
    "Technology achievement: Digital Transformation in Public and Private Sectors": """
    Banks have implemented Open Digital Banking platforms and paperless initiatives.
    For example, UBA's Leo chatbot became a digital persona for automated service across social media platforms.
    [Source: Tony Elumelu Foundation, Apr 2023](https://www.tonyelumelufoundation.org/wp-content/uploads/dlm_uploads/2022/08/The-Future-of-Technology-and-Innovation-in-Nigeria.pdf)
    """,
    "Technology achievement: Digital Identity and Financial Inclusion": """
    Initiatives like the National Identification Number (NIN) and Bank Verification Number (BVN) leverage technology to formalize identity and expand financial services.
    """,

    # Health achievement: Health Sector Renewal Investment Initiative
    "Health achievement: Health Sector Renewal Investment Initiative": """
    A strategic blueprint launched by the Ministry of Health and Social Welfare (FMOHSW) to improve population health outcomes, particularly through primary healthcare and enhancing reproductive, maternal, and child health services.
    This includes a compact signed with all 36 states and the FCT.
    [Source: FMOHSW Ministerial Briefing, May 2024](https://fmino.gov.ng/achievements-in-the-health-sector-presentation-by-the-hon-cmhsw-muhammad-ali-pate-con-at-the-ministerial-sectoral-briefing-radio-house-abuja-may-24-2024/)
    """,
    "Health achievement: Free Caesarean Sections": """
    Groundbreaking innovations like the Maternal and Newborn Mortality Reduction Initiative offer free caesarean sections to eligible Nigerian women, significantly reducing maternal and newborn mortality.
    [Source: Punch Newspapers, Jan 2025](https://punchng.com/a-stellar-year-for-nigerias-health-sector/)
    """,
    "Health achievement: Retraining of Health Workers": """
    Over 53,000 frontline health workers have been retrained to deliver integrated, high-quality services.
    Plans are in place to equip at least 120,000 frontline health workers serving rural populations over the next three years.
    [Source: FMOHSW Ministerial Briefing, May 2024](https://fmino.gov.ng/achievements-in-the-health-sector-presentation-by-the-hon-cmhsw-muhammad-ali-pate-con-at-the-ministerial-sectoral-briefing-radio-house-abuja-may-24-2024/)
    """,
    "Health achievement: Expanded Health Coverage (BHCPF)": """
    The Basic Health Care Provision Fund (BHCPF) was redesigned and now covers approximately 10 million Nigerians, with a record 2.4 million citizens enrolling in the national health insurance scheme, enhancing access to affordable healthcare.
    [Source: Punch Newspapers, Jan 2025](https://punchng.com/a-stellar-year-for-nigerias-health-sector/)
    """,
    "Health achievement: Revenue and Investment Attraction": """
    The sector has secured significant financing mechanisms, including a €1 billion European Investment Bank financing and a $1 billion Afreximbank financing to support incoming manufacturers in the health and life sciences sectors.
    Over 70 new healthcare manufacturing companies are in discussions, with 22 large-scale projects actively engaging international financiers.
    [Source: Punch Newspapers, Jan 2025](https://punchng.com/a-stellar-year-for-nigerias-health-sector/)
    """,
    "Health achievement: Local Manufacturing Initiatives": """
    The Presidential Unlocking Healthcare Value Chain Initiative aims to increase local manufacturing of rapid diagnostic tests (e.g., Abbott Diagnostics plant), medical oxygen (e.g., Global Gases group plant), essential antibiotics (e.g., Jawa Investments producing Amoxicillin-Clavulanic Acid locally), vaccines, and other health solutions.
    [Source: Punch Newspapers, Jan 2025](https://punchng.com/a-stellar-year-for-nigerias-health-sector/)
    """,
    "Health achievement: Vaccination Campaigns": """
    * Over 5 million Nigerian children vaccinated against diphtheria.
    * More than 10 million received tetanus and diphtheria vaccines.
    * Over 5 million received measles vaccines.
    * Additionally, 4.95 million girls (9-14 years) in 15 states received HPV vaccines (80% target achieved in some areas), with plans for 6 million more.
    [Source: FMOHSW Ministerial Briefing, May 2024](https://fmino.gov.ng/achievements-in-the-health-sector-presentation-by-the-hon-cmhsw-muhammad-ali-pate-con-at-the-ministerial-sectoral-briefing-radio-house-abuja-may-24-2024/)
    """,
    "Health achievement: New Hospitals and Infrastructure": """
    * Federal hospitals successfully executed 201 specific infrastructure projects in the last year.
    * 179 specific pieces of important medical equipment were procured and distributed across the six geopolitical zones.
    * At least 1,400 Primary Health Care Centers are now equipped to provide skilled birth attendance.
    [Source: FMOHSW Ministerial Briefing, May 2024](https://fmino.gov.ng/achievements-in-the-health-sector-presentation-by-the-hon-cmhsw-muhammad-ali-pate-con-at-the-ministerial-sectoral-briefing-radio-house-abuja-may-24-2024/)
    """,
    "Health achievement: Human Resources for Health recruitment": """
    Over 2,400 health workers (nurses, doctors, midwives) have been recruited to provide services.
    The intake capacity of medical and nursing schools has significantly increased from 28,000 to 64,000 annually.
    [Source: FMOHSW Ministerial Briefing, May 2024](https://fmino.gov.ng/achievements-in-the-health-sector-presentation-by-the-hon-cmhsw-muhammad-ali-pate-con-at-the-ministerial-sectoral-briefing-radio-house-abuja-may-24-2024/)
    """,
    # Infrastructure achievement: Road and Highway Expansion
    "Infrastructure achievement: Road and Highway Expansion": """
    Major construction projects have improved transportation networks across the country, easing congestion and boosting trade.
    Significant progress has been noted in road and highway expansion in 2024, improving connectivity across urban and rural areas.
    [Source: The Estero, Feb 2025](https://www.olaniwunajayi.net/blog/nigerias-infrastructure-growth-in-2024-key-developments-and-2025-outlook/)
    """,
    "Infrastructure achievement: Railway Upgrades and Modernization": """
    Expanded rail lines now connect key cities, reducing travel time and supporting economic activity.
    The government's commitment to modernizing transport networks aligns with long-term economic development goals.
    [Source: The Estero, Feb 2025](https://www.olaniwunajayi.net/blog/nigerias-infrastructure-growth-in-2024-key-developments-and-2025-outlook/)
    """,
    "Infrastructure achievement: Airport Development": """
    Renovation and expansion of international airports (e.g., Lagos, Abuja, Kano, Port Harcourt) with new terminals, aiming to improve passenger experience and cargo handling.
    """,
    "Infrastructure achievement: Port Modernization": """
    Efforts to modernize seaports to enhance efficiency, reduce congestion, and boost trade facilitation, including ongoing deep seaport projects like the Lekki Deep Seaport, which is expected to significantly boost cargo handling capacity.
    """,
    "Infrastructure achievement: Power Sector Reforms and Projects": """
    Ongoing efforts to improve electricity generation, transmission, and distribution, with investments in new power plants and efforts to improve grid stability.
    The Presidential Power Initiative (PPI) aims to upgrade the national grid.
    """,
    "Infrastructure achievement: Urban Development and Housing": """
    Investments in sustainable housing initiatives and smart city projects are reshaping Nigeria's urban landscape, with a focus on affordable housing.
    Developers are leveraging innovative construction methods to reduce costs and improve efficiency.
    [Source: The Estero, Feb 2025](https://www.olaniwunajayi.net/blog/nigerias-infrastructure-growth-in-2024-key-developments-and-2025-outlook/)
    """,
    "Infrastructure achievement: Telecommunications Infrastructure": """
    Rapid growth in broadband penetration and the rollout of 5G technology in major cities have strengthened connectivity and accelerated digital transformation.
    Improved broadband penetration and government-backed digital inclusion initiatives are strengthening Nigeria's position as a key player in Africa's digital economy.
    [Source: The Estero, Feb 2025](https://www.olaniwunajayi.net/blog/nigerias-infrastructure-growth-in-2024-key-developments-and-2025-outlook/)
    """,
    "Infrastructure achievement: Public-Private Partnerships (PPPs)": """
    The government is strengthening PPP frameworks to attract private investment and ensure sustainable project financing across various infrastructure sectors.
    Reforms in construction regulations and land acquisition laws are part of this effort, making large-scale developments more feasible.
    [Source: The Estero, Feb 2025](https://www.olaniwunajayi.net/blog/nigerias-infrastructure-growth-in-2024-key-developments-and-2025-outlook/)
    """,
    "Infrastructure achievement: Revival of Stalled Projects": """
    Commitment to completing and reviving previously stalled infrastructure projects, demonstrating dedication to continuity in development.
    """,
    "Infrastructure achievement: Bridges and Flyovers": """
    Construction of major bridges and flyovers in urban centers (e.g., Lagos) to ease traffic congestion and improve urban mobility.
    """,

}
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
