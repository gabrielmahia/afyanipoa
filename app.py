# Copyright (c) 2026 Gabriel Mahia / AI Kung Fu LLC. MIT License.
# afyanipoa — Community Health Worker AI Co-Pilot
# Research basis:
#   arXiv:2408.17216 "Democratizing AI in Africa: Federated Learning for Low-Resource Edge Devices" (2024)
#   "Edge intelligence unleashed: deploying LLMs in resource-constrained environments" (2025)
#   arXiv:2601.09716 "NLP Opportunities and Challenges for African Languages" (2026)
#   WHO CHW Reference Group: "Community Health Workers Delivering Primary Health Care" (2022)
# First in Kenya: Swahili-language AI decision-support tool for 105,000+ Kenya CHWs (CHEWs)
# =============================================================================

import streamlit as st
import urllib.request
import json

st.set_page_config(
    page_title="Afyanipoa — Msaada wa Afya",
    page_icon="🏥",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
  .stApp { background: #002b36; }
  .title { font-size:1.5rem; font-weight:800; color:#2196f3; text-align:center; }
  .sub   { font-size:0.82rem; color:#64b5f6; text-align:center; margin-bottom:1rem; }
  .card  { background:#003542; border:1px solid #0277bd; border-radius:8px; padding:12px; margin:6px 0; }
  .demo-tag { background:#d32f2f; color:#fff; font-size:0.6rem; padding:2px 6px; border-radius:3px; }
  .warn  { background:#3e2723; border:1px solid #bf360c; border-radius:6px; padding:8px; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="title">🏥 Afyanipoa — AI kwa CHW</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub">Msaada wa AI kwa Wahudumu wa Afya wa Jamii (CHW) '
    '<span class="demo-tag">DEMO — Si uamuzi wa daktari</span></div>',
    unsafe_allow_html=True
)

# ── API Key ───────────────────────────────────────────────────────────────────
API_KEY = st.secrets.get("GOOGLE_API_KEY") or st.secrets.get("GEMINI_API_KEY", "")
if not API_KEY:
    st.warning(
        "⚠️ **Huduma hii bado haijaungwa.** / This service is not yet configured. "
        "Please check back soon."
    )
    st.stop()

# ── CHW Knowledge Base (DEMO — embedded, no internet needed) ─────────────────
# Source: "DEMO — Synthetic guidelines representative of Kenya MOH CHW training materials"
# Real: Kenya MOH CHEW Curriculum + WHO Integrated Management of Childhood Illness (IMCI)

PROTOCOLS = {
    "🤒 Homa / Fever": {
        "en": "fever",
        "protocol": "DANGER SIGNS: convulsions, stiff neck, difficulty breathing → refer immediately. "
                    "Simple fever (<5d, no danger signs): paracetamol, ORS, follow up in 3 days. "
                    "Malaria risk area: use RDT if available. Positive RDT: AL per weight/age.",
        "protocol_sw": "ISHARA ZA HATARI: mshtuko, shingo ngumu, ugumu wa kupumua → peleka hospitali sasa. "
                       "Homa rahisi: paracetamol, maji ya ORS, fuatilia baada ya siku 3. "
                       "Eneo la malaria: tumia RDT. Chanya: toa AL kwa uzito/umri.",
        "referral_triggers": ["convulsions", "stiff neck", "difficulty breathing", "temp > 39.5", "under 2 months"],
        "keyword": ["homa","fever","joto","mtetemeko"]
    },
    "🤧 Kikohozi / Cough": {
        "en": "cough",
        "protocol": "Count breaths for 60 seconds. Fast breathing: ≥50 (<12mo), ≥40 (12-60mo). "
                    "Fast breathing OR chest indrawing OR wheeze → refer. "
                    "No danger signs: honey + warm water (>1yr), follow up 3 days.",
        "protocol_sw": "Hesabu pumzi kwa sekunde 60. Pumzi za haraka: ≥50 (chini ya mwaka 1), ≥40 (mwaka 1-5). "
                       "Pumzi za haraka AU kifua kushuka ndani AU kupiga mishipa → peleka hospitali. "
                       "Hakuna ishara ya hatari: asali na maji ya joto (>mwaka 1), fuatilia siku 3.",
        "referral_triggers": ["fast breathing", "chest indrawing", "wheeze", "blood in sputum"],
        "keyword": ["kikohozi","cough","pumzi","kupumua"]
    },
    "💧 Kuhara / Diarrhoea": {
        "en": "diarrhoea",
        "protocol": "Count stools per day. Assess dehydration: sunken eyes, dry mouth, skin pinch slow. "
                    "Severe dehydration → refer IMMEDIATELY with ORS on the way. "
                    "Some dehydration: ORS 75ml/kg over 4hrs, monitor. "
                    "No dehydration: ORS + zinc 10-20mg x 14 days + continue feeding.",
        "protocol_sw": "Hesabu choo kwa siku. Angalia upungufu wa maji: macho yaliyozama, kinywa kikavu, ngozi kurejea polepole. "
                       "Upungufu mkubwa → peleka hospitali SASA na ORS njiani. "
                       "Upungufu wastani: ORS 75ml/kg kwa masaa 4. "
                       "Bila upungufu: ORS + zinki siku 14 + endelea kulisha.",
        "referral_triggers": ["blood in stool", "unable to drink", "sunken eyes", "lethargic"],
        "keyword": ["kuhara","diarrhoea","choo","tumbo"]
    },
    "🤰 Mama Mjamzito / ANC": {
        "en": "antenatal",
        "protocol": "First ANC visit by 12 weeks. Minimum 8 contacts (WHO 2016 ANC model). "
                    "Danger signs: bleeding, severe headache, visual disturbance, convulsions, "
                    "no fetal movement → refer IMMEDIATELY. "
                    "Routine: iron-folic acid daily, ITN, TT vaccination, IPTp from 13wks.",
        "protocol_sw": "ANC ya kwanza kabla ya wiki 12. ANC 8 angalau (mfano wa WHO 2016). "
                       "Ishara za hatari: kutoka damu, maumivu ya kichwa, kuona vibaya, mshtuko, "
                       "mtoto kusogea → peleka hospitali SASA. "
                       "Kawaida: chuma-foliki kila siku, neti ya mbu, chanjo ya TT, IPTp tangu wiki 13.",
        "referral_triggers": ["bleeding", "severe headache", "visual disturbance", "convulsions", "no movement"],
        "keyword": ["mjamzito","ujauzito","antenatal","ANC","mimba"]
    },
    "🍼 Lishe / Malnutrition": {
        "en": "malnutrition",
        "protocol": "MUAC screening: Red (<11.5cm) → severe acute malnutrition (SAM) → refer for RUTF. "
                    "Yellow (11.5-12.5cm) → moderate (MAM) → supplementary food + monthly monitoring. "
                    "Check for bilateral pitting oedema (kwashiorkor sign) → refer if present. "
                    "Counsel on IYCF: exclusive breastfeeding 6 months, complementary from 6 months.",
        "protocol_sw": "Pima MUAC: Nyekundu (<11.5cm) → utapiamlo mkali → peleka kwa RUTF. "
                       "Njano (11.5-12.5cm) → wastani → chakula cha ziada + ufuatiliaji kila mwezi. "
                       "Angalia uvimbe wa miguu (ishara ya kwashiorkor) → peleka kama unaonekana. "
                       "Eleza IYCF: kunyonyesha peke yake miezi 6, chakula kingi zaidi kuanzia miezi 6.",
        "referral_triggers": ["MUAC < 11.5", "bilateral oedema", "not eating", "not responding"],
        "keyword": ["lishe","malnutrition","chakula","muac","njaa"]
    }
}

EMERGENCY_CONTACTS = """
📞 **Nambari za dharura (Emergency contacts):**
- Kenya MOH Helpline: 0800 720 571 (bure/free)
- Poison Control: 0800 723 253 (bure/free)
- Referral hospitals: Kenyatta National, Moi Teaching, county referrals
"""

# ── UI ────────────────────────────────────────────────────────────────────────
st.markdown('<div class="card">', unsafe_allow_html=True)
col1, col2 = st.columns([2,1])
with col1:
    complaint = st.text_area(
        "📋 Tatizo la mgonjwa (Patient complaint)",
        placeholder="Mfano: Mtoto wa miaka 3 ana homa, kikohozi na upumzaji wa haraka siku 2...\n"
                    "Example: 3-year-old has fever, cough and fast breathing for 2 days...",
        height=100
    )
with col2:
    patient_age = st.text_input("👶 Umri (Age)", placeholder="e.g. 3y, 6mo")
    lang = st.radio("🌐 Lugha", ["Kiswahili", "English"], horizontal=True)
st.markdown("</div>", unsafe_allow_html=True)

# Quick protocol buttons
st.markdown("**Chagua haraka (Quick select):**")
btn_cols = st.columns(len(PROTOCOLS))
selected_protocol = None
for idx, (name, _) in enumerate(PROTOCOLS.items()):
    if btn_cols[idx].button(name, key=f"prot_{idx}"):
        selected_protocol = name

if st.button("🔍 Tafuta Mwongozo (Get Guidance)", type="primary") and complaint.strip():
    with st.spinner("Inachambua dalili... / Analyzing symptoms..."):
        lang_instr = ("Respond entirely in Swahili (Kiswahili). Use simple language a CHW with basic training understands."
                      if lang == "Kiswahili"
                      else "Respond in simple English. Avoid medical jargon where possible.")

        # Find matching protocol
        complaint_lower = complaint.lower()
        matched = []
        for prot_name, prot_data in PROTOCOLS.items():
            if any(kw in complaint_lower for kw in prot_data["keyword"]):
                matched.append(prot_name)

        protocol_context = ""
        if matched:
            for m in matched[:2]:
                p = PROTOCOLS[m]
                protocol_context += f"\n\n**Kenya MOH Protocol — {m}:**\n"
                protocol_context += p["protocol_sw"] if lang == "Kiswahili" else p["protocol"]
                protocol_context += f"\nReferral triggers: {', '.join(p['referral_triggers'])}"

        system_prompt = f"""You are an AI clinical decision-support assistant for Kenya Community Health Workers (CHEWs).
You use Kenya MOH protocols and WHO guidelines.
{lang_instr}

CRITICAL RULES:
1. You are NOT a doctor. Always recommend referring to a health facility when in doubt.
2. Always check for danger signs FIRST.
3. Always include the emergency helpline (0800 720 571) for serious cases.
4. This is educational decision support — the CHW and the health system make the final call.

Patient age: {patient_age or "not specified"}

Reference protocols available:{protocol_context}

Respond in this structure:
1. ISHARA ZA HATARI / DANGER SIGNS (check first)
2. TATHMINI / ASSESSMENT (what to check)
3. MATIBABU / IMMEDIATE ACTION
4. PELEKA / REFERRAL (when to refer)
5. FUATILIA / FOLLOW-UP

Keep response concise — CHWs in the field need fast, clear guidance."""

        payload = {
            "model": "gemini-2.0-flash",
            "contents": [{"parts": [{"text": f"CHW asks: {complaint}\nPatient age: {patient_age or 'unknown'}"}]}],
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "generation_config": {"temperature": 0.2, "max_output_tokens": 600}
        }
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={API_KEY}"
        req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                      method="POST", headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                resp = json.loads(r.read())
            guidance = resp["candidates"][0]["content"]["parts"][0]["text"]

            st.markdown("#### 📋 Mwongozo wa Kliniki (Clinical Guidance)")
            st.markdown(f'<div class="card">{guidance}</div>', unsafe_allow_html=True)
            st.info(EMERGENCY_CONTACTS)
            st.markdown(
                '<div class="warn">⚠️ <b>DEMO — Si uamuzi wa daktari.</b> Mwongozo huu ni wa msaada tu. '
                "CHW anafanya uamuzi wa mwisho. / This is decision support only — not a diagnosis. "
                "The CHW and health system make the final clinical decision. "
                "Source: DEMO data representative of Kenya MOH CHW training materials.</div>",
                unsafe_allow_html=True
            )
        except Exception as e:
            st.error(f"Hitilafu ya mfumo / System error: {str(e)[:80]}")

# Show full protocol library
with st.expander("📚 Maktaba ya Itifaki (Full Protocol Library)"):
    for name, data in PROTOCOLS.items():
        st.markdown(f"**{name}**")
        st.markdown(f"{'Kiswahili:' if lang == 'Kiswahili' else 'English:'} {data['protocol_sw'] if lang == 'Kiswahili' else data['protocol']}")
        st.markdown(f"🚨 Peleka kwa: {', '.join(data['referral_triggers'])}")
        st.markdown("---")

st.caption("🏥 afyanipoa · AI Kung Fu LLC · Research: arXiv:2408.17216 | WHO CHW Guidelines | Kenya MOH — DEMO data")
