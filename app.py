import asyncio
import os
import time
from pathlib import Path
from typing import List, Dict

import requests
import streamlit as st
from dotenv import load_dotenv

import inngest


# =====================================================
# LOAD ENV
# =====================================================

load_dotenv()

# =====================================================
# STREAMLIT CONFIG
# =====================================================

st.set_page_config(
    page_title="RAG PDF Assistant",
    page_icon="📄",
    layout="centered"
)

# =====================================================
# INNGEST CLIENT
# =====================================================

@st.cache_resource
def get_inngest_client() -> inngest.Inngest:

    return inngest.Inngest(
        app_id="rag_app",
        is_production=False
    )

# =====================================================
# SAVE PDF
# =====================================================

def save_uploaded_pdf(file) -> Path:

    uploads_dir = Path("uploads")

    uploads_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    file_path = uploads_dir / file.name

    file_path.write_bytes(
        file.getbuffer()
    )

    return file_path

# =====================================================
# SEND INGEST EVENT
# =====================================================

async def send_rag_ingest_event(
    pdf_path: Path
):

    client = get_inngest_client()

    await client.send(
        inngest.Event(
            name="rag/ingest_pdf",
            data={
                "pdf_path": str(
                    pdf_path.resolve()
                ),
                "source_id": pdf_path.name
            }
        )
    )

# =====================================================
# SEND QUERY EVENT
# =====================================================

async def send_rag_query_event(
    question: str,
    top_k: int
):

    client = get_inngest_client()

    result = await client.send(
        inngest.Event(
            name="rag/query_pdf_ai",
            data={
                "question": question,
                "top_k": top_k
            }
        )
    )

    if not result:
        raise RuntimeError(
            "No event returned from Inngest"
        )

    return result[0]

# =====================================================
# INNGEST API BASE
# =====================================================

def get_inngest_api_base():

    return os.getenv(
        "INNGEST_API_BASE",
        "http://127.0.0.1:8288/v1"
    )

# =====================================================
# FETCH RUNS
# =====================================================

def fetch_runs(
    event_id: str
) -> List[Dict]:

    url = (
        f"{get_inngest_api_base()}"
        f"/events/{event_id}/runs"
    )

    response = requests.get(url)

    response.raise_for_status()

    data = response.json()

    return data.get("data", [])

# =====================================================
# WAIT FOR OUTPUT
# =====================================================

def wait_for_run_output(
    event_id: str,
    timeout_s: float = 120.0,
    poll_interval_s: float = 1.0
):

    start = time.time()

    last_status = None

    while True:

        runs = fetch_runs(event_id)

        if runs:

            run = runs[0]

            status = run.get("status")

            last_status = status

            if status in [
                "Completed",
                "Succeeded",
                "Success",
                "Finished"
            ]:

                output = run.get("output")

                if isinstance(output, dict):
                    return output

                return {}

            if status in [
                "Failed",
                "Cancelled"
            ]:

                raise RuntimeError(
                    f"Function run failed: {status}"
                )

        elapsed = time.time() - start

        if elapsed > timeout_s:

            raise TimeoutError(
                f"Timed out waiting for output. "
                f"Last status: {last_status}"
            )

        time.sleep(poll_interval_s)

# =====================================================
# HEADER
# =====================================================

st.title("📄 RAG PDF Assistant")

st.write(
    "Upload PDFs and ask questions "
    "using Retrieval-Augmented Generation."
)

# =====================================================
# PDF UPLOAD SECTION
# =====================================================

st.subheader("Upload PDF")

uploaded = st.file_uploader(
    "Choose a PDF",
    type=["pdf"],
    accept_multiple_files=False
)

if uploaded is not None:

    try:

        with st.spinner(
            "Uploading and ingesting PDF..."
        ):

            path = save_uploaded_pdf(
                uploaded
            )

            asyncio.run(
                send_rag_ingest_event(path)
            )

            time.sleep(0.5)

        st.success(
            f"Ingestion triggered for: {path.name}"
        )

    except Exception as e:

        st.error(
            f"Upload failed: {str(e)}"
        )

# =====================================================
# QUESTION SECTION
# =====================================================

st.divider()

st.subheader("Ask Questions")

with st.form("rag_query_form"):

    question = st.text_input(
        "Your Question"
    )

    top_k = st.slider(
        "Retrieved Chunks",
        min_value=1,
        max_value=20,
        value=5
    )

    submitted = st.form_submit_button(
        "Ask"
    )

# =====================================================
# QUERY EXECUTION
# =====================================================

if submitted:

    if not question.strip():

        st.warning(
            "Please enter a question."
        )

    else:

        try:

            with st.spinner(
                "Searching documents..."
            ):

                event_id = asyncio.run(
                    send_rag_query_event(
                        question.strip(),
                        top_k
                    )
                )

                output = wait_for_run_output(
                    event_id
                )

                answer = output.get(
                    "answer",
                    ""
                )

                sources = output.get(
                    "sources",
                    []
                )

                num_contexts = output.get(
                    "num_contexts",
                    0
                )

            # =========================================
            # ANSWER
            # =========================================

            st.subheader("Answer")

            if answer:

                st.write(answer)

            else:

                st.warning(
                    "No answer generated."
                )

            # =========================================
            # METADATA
            # =========================================

            st.caption(
                f"Retrieved Contexts: {num_contexts}"
            )

            # =========================================
            # SOURCES
            # =========================================

            if sources:

                st.subheader("Sources")

                unique_sources = list(
                    dict.fromkeys(sources)
                )

                for source in unique_sources:

                    st.write(f"- {source}")

        except Exception as e:

            st.error(
                f"Query failed: {str(e)}"
            )