"""Streamlit UI, skirta užpildyti Word šabloną užsakymo duomenimis ir eksportuoti PDF.

Paleidimas:
    streamlit run app.py
"""

from __future__ import annotations

import base64
import tempfile
from datetime import date as date_cls
from decimal import Decimal, InvalidOperation
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
from docxtpl import DocxTemplate

from lt_numbers import price_to_lithuanian_words
from pdf_convert import PdfConversionError, convert_docx_to_pdf


# Lietuviški mėnesių pavadinimai kilmininko linksniu (naudojami datose).
LT_MONTHS_GENITIVE = [
    "sausio",
    "vasario",
    "kovo",
    "balandžio",
    "gegužės",
    "birželio",
    "liepos",
    "rugpjūčio",
    "rugsėjo",
    "spalio",
    "lapkričio",
    "gruodžio",
]


def trigger_browser_download(data: bytes, filename: str, mime: str) -> None:
    """Įterpia paslėptą HTML nuorodą, kuri automatiškai parsisiunčia `data`."""
    b64 = base64.b64encode(data).decode("ascii")
    components.html(
        f"""
        <html><body>
        <a id="auto-dl" href="data:{mime};base64,{b64}"
           download="{filename}"></a>
        <script>
          const a = document.getElementById("auto-dl");
          if (a) {{ a.click(); }}
        </script>
        </body></html>
        """,
        height=0,
    )


def parse_price(raw: str, field_label: str) -> Decimal | None:
    """Konvertuoja tekstą į Decimal arba parodo įspėjimą ir grąžina None."""
    raw = raw.strip()
    if not raw:
        return None
    try:
        return Decimal(raw.replace(",", ".").strip())
    except InvalidOperation:
        st.warning(f"Laukas „{field_label}“ nėra tinkamas skaičius.")
        return None


st.set_page_config(page_title="Užsakymo dokumento pildyklė", page_icon="📄")

st.title("📄 Užsakymo dokumento pildyklė")
st.caption(
    "Įkelkite Word šabloną su Jinja žymomis, įveskite užsakymo duomenis "
    "ir parsisiųskite užpildytą DOCX bei sugeneruotą PDF."
)

with st.expander("Palaikomos šablono žymos", expanded=False):
    st.markdown(
        """
        Savo `.docx` šablone galite naudoti šias Jinja stiliaus žymas:

        | Žyma | Reikšmė |
        | --- | --- |
        | `{{ uzsakymo_numeris }}` | Užsakymo numeris |
        | `{{ vardas_pavarde }}` | Vardas ir pavardė |
        | `{{ adresas }}` | Adresas |
        | `{{ kaina }}` | Kaina, pvz. `1234,56` |
        | `{{ kaina_zodziais }}` | Kaina žodžiais |
        | `{{ terminas }}` | Terminas |
        | `{{ avansas }}` | Avansas, pvz. `1234,56` |
        | `{{ avansas_zodziais }}` | Avansas žodžiais |
        | `{{ antra_kainos_dalis }}` | Antra kainos dalis, pvz. `1234,56` |
        | `{{ antra_kainos_dalis_zodziais }}` | Antra kainos dalis žodžiais |
        | `{{ deklaruota_gyvenamoji_vieta }}` | Deklaruota gyvenamoji vieta |
        | `{{ telefono_numeris }}` | Telefono numeris |
        | `{{ prekiu_pristatymo_adresas }}` | Prekių pristatymo adresas |
        | `{{ metai }}` | Metai (YYYY) — nustatoma automatiškai |
        | `{{ menuo_zodziais }}` | Mėnuo žodžiais — nustatoma automatiškai |
        | `{{ diena }}` | Diena (DD) — nustatoma automatiškai |
        """
    )

st.subheader("Šablonas")
uploaded = st.file_uploader("Word šablonas (.docx)", type=["docx"])

st.subheader("Užsakymo duomenys")
col1, col2 = st.columns(2)
with col1:
    uzsakymo_numeris = st.text_input("Užsakymo numeris", value="")
    vardas_pavarde = st.text_input("Vardas ir pavardė", value="")
    adresas = st.text_input("Adresas", value="")
    deklaruota_gyvenamoji_vieta = st.text_input(
        "Deklaruota gyvenamoji vieta", value=""
    )
    telefono_numeris = st.text_input("Telefono numeris", value="")
    prekiu_pristatymo_adresas = st.text_input(
        "Prekių pristatymo adresas", value=""
    )
with col2:
    kaina_raw = st.text_input(
        "Kaina (EUR)",
        value="",
        help="Kaip skyriklį naudokite tašką arba kablelį, pvz. 1234,56",
    )
    avansas_raw = st.text_input(
        "Avansas (EUR)",
        value="",
        help="Kaip skyriklį naudokite tašką arba kablelį, pvz. 500,00",
    )
    antra_kainos_dalis_raw = st.text_input(
        "Antra kainos dalis (EUR)",
        value="",
        help="Kaip skyriklį naudokite tašką arba kablelį",
    )
    terminas = st.text_input("Terminas", value="")

# Kainų peržiūra žodžiais.
kaina = parse_price(kaina_raw, "Kaina")
if kaina is not None:
    st.info(f"**Kaina žodžiais:** {price_to_lithuanian_words(kaina)}")

avansas = parse_price(avansas_raw, "Avansas")
if avansas is not None:
    st.info(f"**Avansas žodžiais:** {price_to_lithuanian_words(avansas)}")

antra_kainos_dalis = parse_price(antra_kainos_dalis_raw, "Antra kainos dalis")
if antra_kainos_dalis is not None:
    st.info(
        "**Antra kainos dalis žodžiais:** "
        f"{price_to_lithuanian_words(antra_kainos_dalis)}"
    )

# Data nustatoma automatiškai pagal sistemos datą.
today = date_cls.today()
metai = f"{today.year:04d}"
menuo_zodziais = LT_MONTHS_GENITIVE[today.month - 1]
diena = f"{today.day:02d}"

st.caption(
    f"Data (nustatoma automatiškai): **{metai} m. {menuo_zodziais} {diena} d.**"
)

proceed = st.button("Tęsti ir generuoti", type="primary")

if proceed:
    if not uploaded:
        st.error("Pirmiausia įkelkite Word šabloną.")
        st.stop()
    if not uzsakymo_numeris.strip():
        st.error("Užsakymo numeris yra privalomas.")
        st.stop()
    if kaina is None:
        st.error("Reikalinga tinkama kaina.")
        st.stop()
    if avansas is None:
        st.error("Reikalingas tinkamas avansas.")
        st.stop()
    if antra_kainos_dalis is None:
        st.error("Reikalinga tinkama antra kainos dalis.")
        st.stop()

    def fmt_eur(value: Decimal) -> str:
        return f"{value:.2f}".replace(".", ",")

    context = {
        "uzsakymo_numeris": uzsakymo_numeris.strip(),
        "vardas_pavarde": vardas_pavarde.strip(),
        "adresas": adresas.strip(),
        "kaina": fmt_eur(kaina),
        "kaina_zodziais": price_to_lithuanian_words(kaina),
        "terminas": terminas.strip(),
        "avansas": fmt_eur(avansas),
        "avansas_zodziais": price_to_lithuanian_words(avansas),
        "antra_kainos_dalis": fmt_eur(antra_kainos_dalis),
        "antra_kainos_dalis_zodziais": price_to_lithuanian_words(
            antra_kainos_dalis
        ),
        "deklaruota_gyvenamoji_vieta": deklaruota_gyvenamoji_vieta.strip(),
        "telefono_numeris": telefono_numeris.strip(),
        "prekiu_pristatymo_adresas": prekiu_pristatymo_adresas.strip(),
        "metai": metai,
        "menuo_zodziais": menuo_zodziais,
        "diena": diena,
    }

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        src_path = tmp_dir / "template.docx"
        src_path.write_bytes(uploaded.getvalue())

        base_name = (
            f"uzsakymas_{uzsakymo_numeris.strip()}_{today.strftime('%Y%m%d')}"
        )
        filled_docx = tmp_dir / f"{base_name}.docx"
        filled_pdf = tmp_dir / f"{base_name}.pdf"

        try:
            doc = DocxTemplate(str(src_path))
            doc.render(context)
            doc.save(str(filled_docx))
        except Exception as exc:  # noqa: BLE001 - parodyti bet kokią šablono klaidą
            st.error(f"Nepavyko užpildyti šablono: {exc}")
            st.stop()

        st.success("Šablonas užpildytas.")
        st.download_button(
            "⬇️ Parsisiųsti užpildytą DOCX",
            data=filled_docx.read_bytes(),
            file_name=filled_docx.name,
            mime=(
                "application/vnd.openxmlformats-officedocument."
                "wordprocessingml.document"
            ),
        )

        with st.spinner("Konvertuojama į PDF..."):
            try:
                convert_docx_to_pdf(filled_docx, filled_pdf)
            except PdfConversionError as exc:
                st.error(str(exc))
                st.stop()

        pdf_bytes = filled_pdf.read_bytes()
        st.success(
            f"PDF sugeneruotas. Parsisiunčiama **{filled_pdf.name}**..."
        )

        # Automatiškai paleidžia parsisiuntimą naršyklėje.
        trigger_browser_download(pdf_bytes, filled_pdf.name, "application/pdf")

        # Atsarginis variantas, jei naršyklė blokuoja automatinį parsisiuntimą.
        st.download_button(
            "⬇️ Parsisiųsti PDF dar kartą",
            data=pdf_bytes,
            file_name=filled_pdf.name,
            mime="application/pdf",
        )
