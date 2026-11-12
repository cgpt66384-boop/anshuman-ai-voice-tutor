
import streamlit as st
import requests
import json
import io
import speech_recognition as sr
import fitz
import streamlit.components.v1 as components

# ==================================
# ANSHUMAN AI - ANDROID EDITION
# ==================================

st.set_page_config(
    page_title="ANSHUMAN AI",
    page_icon="🎓",
    layout="centered"
)

API = "https://vexa-ai.pages.dev"

SYSTEM_PROMPT = """
You are ANSHUMAN AI, a personal AI teacher.

Teach the user everything in very easy English.

RULES:
1. Answer directly.
2. Explain concepts step by step.
3. Use simple words.
4. Give small practical examples.
5. Explain difficult technical terms.
6. Teach like a patient personal teacher.
7. Explain programming code clearly.
8. Never assume the user already knows a topic.
9. Avoid unnecessary complicated language.
10. Keep answers organised with headings and examples.
11. If the user asks for more detail, explain further.
"""

# ==================================
# DESIGN
# ==================================

st.markdown("""
<style>
.stApp {
    background: #10121c;
    color: white;
}
h1 {
    color: #b6a5ff;
    text-align: center;
}
.subtitle {
    text-align: center;
    color: #a9a9bb;
}
.stChatMessage {
    border-radius: 15px;
}
.stButton button {
    border-radius: 12px;
    background: #6246ea;
    color: white;
    border: none;
    width: 100%;
}
</style>
""", unsafe_allow_html=True)

st.title("🎓 ANSHUMAN AI")
st.markdown(
    '<p class="subtitle">Your Personal AI Voice Tutor</p>',
    unsafe_allow_html=True
)

st.caption("Ask anything. Learn everything. Understand easily.")

# ==================================
# SESSION MEMORY
# ==================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "last_answer" not in st.session_state:
    st.session_state.last_answer = ""

# ==================================
# AI CHAT CONNECTION
# ==================================

def ai_chat(messages):

    response = requests.post(
        API + "/chat",
        json={
            "model": "vexa",
            "messages": messages
        },
        stream=True,
        timeout=(20, 180)
    )

    response.raise_for_status()

    for line in response.iter_lines(decode_unicode=True):

        if not line or not line.startswith("data:"):
            continue

        data = line[5:].strip()

        if data == "[DONE]":
            break

        try:
            event = json.loads(data)

            if "error" in event:
                raise RuntimeError(event["error"].get(
                    "message", "AI service error"
                ))

            choices = event.get("choices", [])

            if choices:
                content = choices[0].get(
                    "delta", {}
                ).get("content", "")

                if content:
                    yield content

        except json.JSONDecodeError:
            continue

# ==================================
# SCREENSHOT UNDERSTANDING
# ==================================

def analyse_image(uploaded_image):

    result = requests.post(
        API + "/visual",
        data={
            "prompt": (
                "Explain everything visible in this image "
                "in very easy English, step by step. "
                "Explain diagrams, text and code."
            ),
            "template": "code_beginner"
        },
        files={
            "image": (
                uploaded_image.name,
                uploaded_image.getvalue(),
                uploaded_image.type
            )
        },
        timeout=180
    )

    result.raise_for_status()
    data = result.json()

    if not data.get("success"):
        raise RuntimeError(data.get("error", "Image analysis failed"))

    return data["response"]

# ==================================
# PDF READER
# ==================================

def read_pdf(uploaded_pdf):

    document = fitz.open(
        stream=uploaded_pdf.getvalue(),
        filetype="pdf"
    )

    pages = []

    for page in document:
        pages.append(page.get_text())

    document.close()

    return "\n".join(pages)[:12000]

# ==================================
# VOICE RECOGNITION
# ==================================

def transcribe_voice(audio):

    recognizer = sr.Recognizer()

    with sr.AudioFile(io.BytesIO(audio.getvalue())) as source:
        audio_data = recognizer.record(source)

    return recognizer.recognize_google(
        audio_data,
        language="en-IN"
    )

# ==================================
# VOICE OUTPUT
# ==================================

def speak(text):

    safe_text = json.dumps(text).replace("</", "<\\/")

    html = """
    <div style="background:#20243a;padding:12px;border-radius:12px;">
      <button id="speak"
      style="background:#6246ea;color:white;border:0;
      padding:12px;border-radius:10px;width:100%;font-size:16px;">
      🔊 Speak Answer
      </button>
      <button id="stop"
      style="background:#444;color:white;border:0;
      padding:10px;border-radius:10px;width:100%;margin-top:8px;">
      ⏹ Stop Speaking
      </button>
    </div>
    <script>
    const answer = """ + safe_text + """;

    document.getElementById("speak").onclick = () => {
      window.speechSynthesis.cancel();
      const speech = new SpeechSynthesisUtterance(answer);
      speech.lang = "en-IN";
      speech.rate = 0.92;
      window.speechSynthesis.speak(speech);
    };

    document.getElementById("stop").onclick = () => {
      window.speechSynthesis.cancel();
    };
    </script>
    """

    components.html(html, height=115)

# ==================================
# SIDEBAR
# ==================================

with st.sidebar:

    st.header("⚙️ Settings")

    voice_enabled = st.toggle(
        "Enable voice answers",
        value=True
    )

    st.divider()

    st.subheader("📄 Study PDF")

    pdf_file = st.file_uploader(
        "Upload your study PDF",
        type=["pdf"]
    )

    pdf_text = ""

    if pdf_file:
        try:
            pdf_text = read_pdf(pdf_file)
            st.success("PDF loaded!")
        except Exception as e:
            st.error(f"PDF error: {e}")

    st.divider()

    st.subheader("🖼️ Screenshot learning")

    image_file = st.file_uploader(
        "Upload a screenshot",
        type=["png", "jpg", "jpeg"]
    )

    if image_file:
        st.image(image_file, caption="Uploaded screenshot")

    st.divider()

    if st.button("🗑️ Clear conversation"):
        st.session_state.messages = []
        st.session_state.last_answer = ""
        st.rerun()

# ==================================
# CHAT HISTORY
# ==================================

for message in st.session_state.messages:

    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ==================================
# TEXT QUESTION
# ==================================

question = st.chat_input("Ask your personal teacher...")

if question:

    user_content = question

    with st.spinner("ANSHUMAN AI is studying your question..."):

        try:

            if image_file:
                image_explanation = analyse_image(image_file)
                user_content += (
                    "\n\nSCREENSHOT EXPLANATION:\n"
                    + image_explanation
                )

            if pdf_text:
                user_content += (
                    "\n\nSTUDY PDF CONTENT:\n"
                    + pdf_text
                )

            st.session_state.messages.append({
                "role": "user",
                "content": user_content
            })

            with st.chat_message("assistant"):

                conversation = [
                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT
                    }
                ] + st.session_state.messages[-12:]

                answer = st.write_stream(
                    ai_chat(conversation)
                )

            st.session_state.messages.append({
                "role": "assistant",
                "content": answer
            })

            st.session_state.last_answer = answer

            st.rerun()

        except Exception as e:
            st.error(f"Something went wrong: {e}")

# ==================================
# VOICE QUESTION
# ==================================

st.divider()

st.subheader("🎙️ Talk to ANSHUMAN AI")

audio = st.audio_input("Tap to record your question")

if audio and st.button("🎧 Ask using my voice"):

    try:

        with st.spinner("Understanding your voice..."):

            spoken_question = transcribe_voice(audio)

        st.success("You said: " + spoken_question)

        user_content = spoken_question

        if pdf_text:
            user_content += (
                "\n\nSTUDY PDF CONTENT:\n" + pdf_text
            )

        if image_file:
            user_content += (
                "\n\nSCREENSHOT EXPLANATION:\n"
                + analyse_image(image_file)
            )

        st.session_state.messages.append({
            "role": "user",
            "content": user_content
        })

        with st.spinner("Preparing your lesson..."):

            conversation = [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                }
            ] + st.session_state.messages[-12:]

            answer = "".join(ai_chat(conversation))

        st.session_state.messages.append({
            "role": "assistant",
            "content": answer
        })

        st.session_state.last_answer = answer

        st.rerun()

    except Exception as e:
        st.error(f"Voice error: {e}")

# ==================================
# SPEAK ANSWER
# ==================================

if voice_enabled and st.session_state.last_answer:

    speak(st.session_state.last_answer)

st.divider()

st.caption("ANSHUMAN AI | Built for learning")
        
