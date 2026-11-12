
import streamlit as st
import requests
import base64
import tempfile
import os
import fitz
import pyttsx3
from faster_whisper import WhisperModel

# ---------------- CONFIGURATION ----------------

st.set_page_config(
    page_title="ANSHUMAN AI",
    page_icon="🎓",
    layout="wide"
)

OLLAMA_URL = "http://localhost:11434/api/chat"
TEXT_MODEL = "qwen2.5:3b"
VISION_MODEL = "llava:7b"

# ---------------- DESIGN ----------------

st.markdown("""
<style>
.stApp {
    background: #10131c;
    color: white;
}
h1, h2, h3 {
    color: #a5b4fc;
}
.stButton button {
    border-radius: 12px;
    background: #5145cd;
    color: white;
    border: none;
}
</style>
""", unsafe_allow_html=True)

st.title("🎓 ANSHUMAN AI")
st.caption("Your Personal AI Voice Tutor")
st.write("Learn anything. Ask anything. Understand everything.")

# ---------------- SESSION MEMORY ----------------

if "messages" not in st.session_state:
    st.session_state.messages = []

if "last_answer" not in st.session_state:
    st.session_state.last_answer = ""

# ---------------- AI INSTRUCTIONS ----------------

SYSTEM_PROMPT = """
You are ANSHUMAN AI, my personal teacher.

Your job is to teach me everything in very easy language.

RULES:
1. Use simple English.
2. Explain difficult topics step by step.
3. Give small and practical examples.
4. Explain technical words.
5. Answer questions directly.
6. Avoid unnecessary long explanations.
7. Teach like a patient personal teacher.
8. Explain programming code clearly.
9. If I upload an image, explain its visible content.
10. If I upload a PDF, answer using its content.
11. Do not ask me to write complicated prompts.
12. If I ask for more detail, explain further.
"""

# ---------------- LOAD SPEECH MODEL ----------------

@st.cache_resource
def load_whisper():
    return WhisperModel("tiny", device="cpu", compute_type="int8")

# ---------------- AI RESPONSE ----------------

def ask_ai(question, image=None, pdf_text=""):

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    messages.extend(st.session_state.messages[-10:])

    content = question

    if pdf_text:
        content += "\n\nPDF CONTENT:\n" + pdf_text[:15000]

    user_message = {
        "role": "user",
        "content": content
    }

    if image:
        image_data = base64.b64encode(image).decode("utf-8")
        user_message["images"] = [image_data]

    messages.append(user_message)

    selected_model = VISION_MODEL if image else TEXT_MODEL

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": selected_model,
            "messages": messages,
            "stream": False
        },
        timeout=300
    )

    response.raise_for_status()

    answer = response.json()["message"]["content"]

    st.session_state.messages.append({
        "role": "user",
        "content": question
    })

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer
    })

    return answer

# ---------------- VOICE OUTPUT ----------------

def speak_answer(text):

    engine = pyttsx3.init()
    engine.setProperty("rate", 165)

    path = os.path.join(tempfile.gettempdir(), "anshuman_ai_voice.wav")

    engine.save_to_file(text, path)
    engine.runAndWait()
    engine.stop()

    return path

# ---------------- SIDEBAR ----------------

with st.sidebar:

    st.header("⚙️ Settings")

    voice_enabled = st.toggle("Speak answers", value=True)

    st.divider()

    st.subheader("📄 Upload PDF")

    pdf_file = st.file_uploader(
        "Choose a PDF",
        type=["pdf"]
    )

    pdf_text = ""

    if pdf_file:
        document = fitz.open(stream=pdf_file.read(), filetype="pdf")
        pdf_text = "\n".join(page.get_text() for page in document)
        st.success("PDF loaded successfully!")

    st.divider()

    st.subheader("🖥️ Screen learning")

    image_file = st.file_uploader(
        "Upload screenshot",
        type=["png", "jpg", "jpeg"]
    )

    if st.button("Clear conversation"):
        st.session_state.messages = []
        st.session_state.last_answer = ""
        st.rerun()

# ---------------- CHAT DISPLAY ----------------

for message in st.session_state.messages:

    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ---------------- TEXT INPUT ----------------

question = st.chat_input("Ask anything. I'll teach you...")

if question:

    with st.spinner("ANSHUMAN AI is thinking..."):

        try:
            image_bytes = image_file.getvalue() if image_file else None

            answer = ask_ai(
                question,
                image=image_bytes,
                pdf_text=pdf_text
            )

            st.session_state.last_answer = answer

            st.rerun()

        except Exception as error:
            st.error(f"Error: {error}")

# ---------------- VOICE INPUT ----------------

st.divider()

st.subheader("🎙️ Talk to ANSHUMAN AI")

audio = st.audio_input("Record your question")

if audio and st.button("Convert voice and ask AI"):

    with st.spinner("Listening to your voice..."):

        try:
            with tempfile.NamedTemporaryFile(
                suffix=".wav",
                delete=False
            ) as file:
                file.write(audio.getvalue())
                audio_path = file.name

            model = load_whisper()
            segments, info = model.transcribe(audio_path)

            spoken_question = " ".join(
                segment.text for segment in segments
            ).strip()

            os.remove(audio_path)

            if not spoken_question:
                st.warning("I could not understand your voice.")
            else:
                st.write("You said:", spoken_question)

                answer = ask_ai(
                    spoken_question,
                    image=image_file.getvalue() if image_file else None,
                    pdf_text=pdf_text
                )

                st.session_state.last_answer = answer
                st.rerun()

        except Exception as error:
            st.error(f"Voice error: {error}")

# ---------------- SPEAK LAST ANSWER ----------------

if voice_enabled and st.session_state.last_answer:

    if st.button("🔊 Speak last answer"):

        with st.spinner("Preparing voice..."):

            try:
                audio_path = speak_answer(
                    st.session_state.last_answer
                )

                with open(audio_path, "rb") as audio_file:
                    st.audio(audio_file.read(), format="audio/wav")

            except Exception as error:
                st.error(f"Voice output error: {error}")

st.caption("ANSHUMAN AI | Personal Learning Project")
