# Dockerfile for running the Streamlit WordTool on Render (or any container host).
#
# Ships Python + LibreOffice so DOCX -> PDF conversion works headless on Linux.
# docx2pdf is intentionally NOT used on Linux (it requires MS Word); pdf_convert.py
# already falls back to LibreOffice via `soffice --headless`.

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# System dependencies:
#   libreoffice-core + libreoffice-writer: minimal LibreOffice for docx -> pdf
#   fonts-*: Unicode/Baltic coverage so Lithuanian glyphs render in the PDF
#   tini: proper PID 1 so SIGTERM from the platform shuts Streamlit down cleanly
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        libreoffice-core \
        libreoffice-writer \
        fonts-liberation \
        fonts-dejavu \
        fonts-dejavu-core \
        fonts-noto-core \
        tini \
        ca-certificates \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first for better layer caching.
COPY requirements.txt ./
RUN pip install -r requirements.txt

# App source.
COPY app.py lt_numbers.py pdf_convert.py ./
COPY .streamlit ./.streamlit
# Optional: bundle the sample template so users have something to try immediately.
COPY templates ./templates

# Render injects $PORT at runtime; default to 8501 for local `docker run`.
ENV PORT=8501
EXPOSE 8501

# Non-root user for a smaller blast radius if anything goes wrong.
RUN useradd --create-home --uid 1000 app \
 && chown -R app:app /app
USER app

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["sh", "-c", "streamlit run app.py --server.address=0.0.0.0 --server.port=${PORT}"]
