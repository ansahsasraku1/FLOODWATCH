import io
from gtts import gTTS
import streamlit as st

def generate_twi_audio(category: str, score: float, landmark: str):
    """
    Generates audio combining dynamic risk results with Twi contextual advice.
    """
    # Map risk level to Twi translation & community advisory
    twi_explanations = {
        "High": f"There is a higher probability that flooding may occur near {landmark} .Please take necessary precautions and be encouraged to stay informed. Also encourage your community to clear debris from drains to reduce flood risk.",
        "Moderately High": f"The chances of flooding near {landmark} are moderate higher, please be cautious . Regular monitoring is advised. You are also encouranged to engage your community to clear debris from drains most especialy in and  around {landmark}.",
        "Moderately": f"There is not much risk of flooding near {landmark} Regular dissilting of drains near {landmark} is recommended to keep the risk of flooding low.",
        "Low": f"Probability of flooding near {landmark} is low. Continuosly encourage your community to maintain drains."
    }

    advice_twi = twi_explanations.get(
        category, 
        ""
    )

    # Construct full script: English key summary + Twi contextual explanation
    full_script = (
        f"Assessment complete. Your location near {landmark} has a flood risk score of {score:.2f}, "
        f"which is classified as {category} risk. "
        f"{advice_twi}"
    )

    # Convert text to audio in-memory
    tts = gTTS(text=full_script, lang='en', tld='com.gh')
    audio_fp = io.BytesIO()
    tts.write_to_fp(audio_fp)
    audio_fp.seek(0)

    return audio_fp