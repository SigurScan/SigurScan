import os
import json
from typing import Dict, Any, List
import re
import logging
import requests

logger = logging.getLogger("gemini_explainer")

# Try importing the Google GenAI SDK
try:
    from google import genai
    from google.genai import types
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False
    logger.warning("google-genai SDK not installed, using fallback explanation generator.")

AI_EXPLAINER_PROVIDER = os.environ.get("AI_EXPLAINER_PROVIDER", "auto").strip().lower()
MISTRAL_ENDPOINT = "https://api.mistral.ai/v1/chat/completions"
MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY", "").strip()
MISTRAL_MODEL = os.environ.get("MISTRAL_MODEL", "mistral-small-latest").strip()


def _extract_json_text(value: str) -> str:
    raw = str(value or "").strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?", "", raw, flags=re.IGNORECASE).strip()
        raw = re.sub(r"```$", "", raw).strip()
    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        return raw[start : end + 1]
    return raw


def _build_prompt(
    text: str,
    rule_results: Dict[str, Any],
    redirect_info: List[Dict[str, Any]] = None
) -> str:
    urls_str = ""
    if redirect_info:
        urls_str = "\n".join([
            f"- Original URL: {info.get('original_url')} -> Final: {info.get('final_url')} (Registered Domain: {info.get('final_registered_domain')})"
            for info in redirect_info
        ])

    return f"""
Ești un asistent cibernetic anti-scam român numit "SigurScan".
Sarcina ta este să analizezi un text suspect și dovezi tehnice, apoi să explici de ce este periculos/suspect în limba română pe un ton clar, calm și prietenos pentru un utilizator non-tehnic.

OBIECTIV CRITIC: Analizează conținutul ofertei sau al acțiunii cerute.
Verifică dacă mesajul conține indicatori de phishing, deturnare de brand, solicitare date sensibile sau acțiuni riscante.

Text suspect primit de utilizator:
"{text}"

Rezultate motor de reguli:
- Scorul de risc: {rule_results.get('risk_score')}/100
- Nivel de risc: {rule_results.get('risk_level')}
- Familia de scam detectată: {rule_results.get('detected_family')}
- Brand pretins: {rule_results.get('claimed_brand')}
- Semnale de alarmă identificate: {", ".join(rule_results.get('reasons', []))}

Redirecționări link-uri:
{urls_str}

Răspunde strict JSON cu exact cheile:
{{
  "verdict_summary": "O frază scurtă despre nivelul de risc.",
  "explanation": "Explicație clară pe limba română.",
  "offer_analysis": "Evaluare scurtă a ofertei și a validității ei.",
  "key_dangers": ["Pericol 1", "Pericol 2"],
  "safe_actions": ["Acțiune 1", "Acțiune 2"]
}}
"""


def _call_mistral(prompt: str) -> Dict[str, Any]:
    if not MISTRAL_API_KEY:
        return {}

    response = requests.post(
        MISTRAL_ENDPOINT,
        headers={
            "Authorization": f"Bearer {MISTRAL_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": MISTRAL_MODEL,
            "temperature": 0.2,
            "max_tokens": 700,
            "messages": [
                {
                    "role": "system",
                    "content": "Ești un asistent cibernetic anti-scam român numit SigurScan.",
                },
                {"role": "user", "content": prompt},
            ],
        },
        timeout=10,
    )
    response.raise_for_status()
    payload = response.json()
    message_content = (
        payload.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
    )
    if not message_content:
        return {}
    parsed = json.loads(_extract_json_text(message_content))
    return parsed if isinstance(parsed, dict) else {}


def _call_gemini(prompt: str) -> Dict[str, Any]:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key or not SDK_AVAILABLE:
        return {}

    # Initialize Google GenAI client (it picks up GEMINI_API_KEY automatically)
    client = genai.Client()
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        )
    )

    response_text = response.text.strip()
    parsed = json.loads(_extract_json_text(response_text))
    return parsed if isinstance(parsed, dict) else {}


def generate_ai_explanation(
    text: str,
    rule_results: Dict[str, Any],
    redirect_info: List[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Uses Mistral or Gemini to generate a friendly, clear, explainable explanation in Romanian.
    If no provider responds, it falls back to a template-based generator.
    """
    prompt = _build_prompt(text, rule_results, redirect_info)

    if AI_EXPLAINER_PROVIDER in {"auto", "mistral"}:
        try:
            data = _call_mistral(prompt)
            if data:
                return {
                    "verdict_summary": data.get("verdict_summary"),
                    "explanation": data.get("explanation"),
                    "offer_analysis": data.get("offer_analysis"),
                    "key_dangers": data.get("key_dangers", []),
                    "safe_actions": data.get("safe_actions", rule_results.get("safe_actions", [])),
                }
            if AI_EXPLAINER_PROVIDER == "mistral":
                return generate_fallback_explanation(text, rule_results)
        except Exception as exc:
            logger.warning("Mistral API error: %s", exc)
            if AI_EXPLAINER_PROVIDER == "mistral":
                return generate_fallback_explanation(text, rule_results)

    if AI_EXPLAINER_PROVIDER == "auto":
        # If auto mode uses Mistral by default and gets no usable response,
        # try Gemini as secondary provider before fallback to templates.
        try:
            data = _call_gemini(prompt)
            if data:
                return {
                    "verdict_summary": data.get("verdict_summary"),
                    "explanation": data.get("explanation"),
                    "offer_analysis": data.get("offer_analysis"),
                    "key_dangers": data.get("key_dangers", []),
                    "safe_actions": data.get("safe_actions", rule_results.get("safe_actions", [])),
                }
        except Exception as e:
            logger.warning("AI explanation failed in auto fallback to Gemini: %s", e)

    if AI_EXPLAINER_PROVIDER == "gemini":
        # Force single-provider flow requested by config.
        try:
            data = _call_gemini(prompt)
            if data:
                return {
                    "verdict_summary": data.get("verdict_summary"),
                    "explanation": data.get("explanation"),
                    "offer_analysis": data.get("offer_analysis"),
                    "key_dangers": data.get("key_dangers", []),
                    "safe_actions": data.get("safe_actions", rule_results.get("safe_actions", []))
                }
        except Exception as e:
            logger.error("Gemini API error: %s. Falling back to rule-based explanation.", e)
            return generate_fallback_explanation(text, rule_results)

    try:
        data = _call_gemini(prompt)
        if data:
            return {
                "verdict_summary": data.get("verdict_summary"),
                "explanation": data.get("explanation"),
                "offer_analysis": data.get("offer_analysis"),
                "key_dangers": data.get("key_dangers", []),
                "safe_actions": data.get("safe_actions", rule_results.get("safe_actions", []))
            }
    except Exception as e:
        logger.error("Gemini fallback error: %s. Falling back to rule-based explanation.", e)

    return generate_fallback_explanation(text, rule_results)

def generate_fallback_explanation(text: str, rule_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Template-based backup generator when Gemini API is unavailable.
    """
    risk_level = rule_results.get("risk_level", "low").upper()
    claimed_brand = rule_results.get("claimed_brand", "Nespecificat")
    family = rule_results.get("detected_family", "Necunoscută")
    reasons = rule_results.get("reasons", [])

    if risk_level in ("CRITICAL", "HIGH"):
        verdict_summary = f"Atenție! Acest mesaj este marcat ca fiind PERICULOS ({family})."
        explanation = f"Analiza automată indică un risc ridicat. Mesajul pretinde că reprezintă brandul '{claimed_brand}', însă semnalele detectate sugerează o tentativă de înșelăciune (phishing). Atacatorii folosesc mesaje alarmante sau linkuri neoficiale pentru a vă induce în eroare."
    elif risk_level == "MEDIUM":
        verdict_summary = f"Atenție: Mesaj suspect ({family})."
        explanation = f"Mesajul conține elemente care seamănă cu o tentativă de scam, menționând brandul '{claimed_brand}'. Vă recomandăm prudență maximă înainte de a accesa orice link sau de a oferi informații."
    else:
        verdict_summary = "Mesaj probabil sigur sau cu risc minim."
        explanation = "Nu au fost detectate elemente evidente de înșelăciune în text. Cu toate acestea, verificați întotdeauna expeditorul înainte de a lua orice acțiune."

    key_dangers = []
    for r in reasons:
        if "card" in r.lower() or "cvc" in r.lower() or "cvv" in r.lower():
            key_dangers.append("Furtul banilor de pe card prin intermediul unor formulare de plată false.")
        elif "whatsapp" in r.lower():
            key_dangers.append("Preluarea contului dumneavoastră de WhatsApp de către atacatori.")
        elif "anydesk" in r.lower() or "teamviewer" in r.lower():
            key_dangers.append("Instalarea de software prin care atacatorii pot controla telefonul de la distanță.")
        elif "mismatch" in r.lower():
            key_dangers.append("Redirecționarea către o pagină web clonă care imită site-ul oficial.")
    
    if not key_dangers:
        key_dangers = [
            "Introducerea de date personale pe pagini neautorizate.",
            "Posibilitatea de a fi indus în eroare de informații false."
        ]

    return {
        "verdict_summary": verdict_summary,
        "explanation": explanation,
        "key_dangers": key_dangers,
        "safe_actions": rule_results.get("safe_actions", [
            "Nu apăsați pe linkuri suspecte.",
            "Nu oferiți nimănui coduri de autentificare sau date bancare.",
            "Verificați manual adresa site-ului oficial în browser."
        ])
    }
