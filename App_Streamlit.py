import streamlit as st
import PyPDF2
import googletrans
from googletrans import Translator
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
import urllib.request
import tempfile
import io
import base64

# Configuration de la page Streamlit
st.set_page_config(
    page_title="Traducteur PDF avec Style BD", page_icon="📚", layout="wide"
)

# Liste des polices BD cool et lisibles disponibles gratuitement
BD_FONTS = [
    {
        "name": "Kalam",
        "url": "https://github.com/google/fonts/raw/main/ofl/kalam/Kalam-Regular.ttf",
        "filename": "Kalam-Regular.ttf",
        "description": "Police manuscrite claire et lisible, parfaite pour les bulles de BD",
    },
    {
        "name": "Acme",
        "url": "https://github.com/google/fonts/raw/main/ofl/acme/Acme-Regular.ttf",
        "filename": "Acme-Regular.ttf",
        "description": "Police sans empattement moderne avec un style BD claire",
    },
    {
        "name": "Neucha",
        "url": "https://github.com/google/fonts/raw/main/ofl/neucha/Neucha-Regular.ttf",
        "filename": "Neucha-Regular.ttf",
        "description": "Police manuscrite informelle avec un caractère BD agréable",
    },
]

# Choisir une police par défaut
DEFAULT_FONT = BD_FONTS[1]


@st.cache_data
def download_bd_font(font_info):
    """Télécharge une police de BD cool et lisible."""
    font_path = os.path.join(tempfile.gettempdir(), font_info["filename"])

    try:
        urllib.request.urlretrieve(font_info["url"], font_path)
        return font_path
    except Exception as e:
        st.error(f"Erreur lors du téléchargement de la police: {e}")
        return None


def extract_text_from_pdf(pdf_file):
    """Extraire le texte d'un fichier PDF."""
    text = ""
    reader = PyPDF2.PdfReader(pdf_file)
    num_pages = len(reader.pages)

    for page_num in range(num_pages):
        page = reader.pages[page_num]
        text += page.extract_text() + "\n"

    return text


def translate_text(text, src_lang="en", dest_lang="fr"):
    """Traduire le texte de la langue source vers la langue cible."""
    translator = Translator()

    # Diviser le texte en morceaux pour éviter les limites de caractères
    chunk_size = 5000
    chunks = [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]

    translated_text = ""
    for chunk in chunks:
        if chunk.strip():  # Éviter de traduire des morceaux vides
            translation = translator.translate(chunk, src=src_lang, dest=dest_lang)
            translated_text += translation.text + " "

    return translated_text


def save_text_to_pdf(
    text,
    bd_font_available=False,
    font_name="BDFrancaise",
    page_format="A4",
    font_size=9,
    margins=24,
):
    """Créer un PDF avec le texte traduit et des paramètres optimisés."""
    # Configuration du format de page
    if page_format == "A4":
        pagesize = A4
    elif page_format == "Letter":
        pagesize = letter
    elif page_format == "Custom Large":
        pagesize = (11 * inch, 17 * inch)  # Format tabloid/ledger

    # Conversion des marges en points
    margins = int(margins)

    # Créer un BytesIO pour stocker le PDF
    buffer = io.BytesIO()

    # Créer le document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=pagesize,
        rightMargin=margins,
        leftMargin=margins,
        topMargin=margins,
        bottomMargin=margins,
    )

    # Créer un style personnalisé avec justification et police
    styles = getSampleStyleSheet()

    # Choisir la police en fonction de sa disponibilité
    font_name = font_name if bd_font_available else "Helvetica"

    # Ajuster la taille de l'espacement entre les lignes en fonction de la taille de police
    leading = font_size * 1.2

    bd_style = ParagraphStyle(
        "BDStyle",
        parent=styles["Normal"],
        fontName=font_name,
        fontSize=font_size,
        alignment=TA_JUSTIFY,
        spaceBefore=font_size / 2,
        spaceAfter=font_size / 2,
        firstLineIndent=font_size,
        leading=leading,
    )

    # Diviser le texte en paragraphes
    paragraphs = text.split("\n")
    story = []

    for paragraph in paragraphs:
        if paragraph.strip():  # Ignorer les paragraphes vides
            p = Paragraph(paragraph, bd_style)
            story.append(p)

    # Construire le PDF
    doc.build(story)

    # Récupérer le contenu du PDF
    pdf_data = buffer.getvalue()
    buffer.close()

    return pdf_data


def create_download_link(pdf_data, filename="traduction.pdf"):
    """Créer un lien de téléchargement pour le PDF généré."""
    b64 = base64.b64encode(pdf_data).decode()
    href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}">Télécharger le PDF traduit</a>'
    return href


def main():
    st.title("🌍 Traducteur PDF avec Style BD 📚")
    st.subheader("Traduisez vos documents PDF et obtenez un résultat avec style BD")

    with st.expander("ℹ️ À propos de cette application", expanded=False):
        st.markdown(
            """
        Cette application vous permet de traduire des documents PDF tout en appliquant un style BD agréable à lire.
        
        **Fonctionnalités:**
        - Traduction de PDF entre différentes langues
        - Application d'une police style BD pour une lecture agréable
        - Optimisation du format de page pour maximiser le contenu
        - Personnalisation de la mise en page
        
        **Comment utiliser:**
        1. Téléchargez votre PDF
        2. Sélectionnez les langues source et cible
        3. Choisissez votre police et les paramètres de mise en page
        4. Lancez la traduction
        5. Téléchargez votre fichier traduit
        """
        )

    # Sidebar pour les paramètres
    st.sidebar.title("⚙️ Paramètres")

    # Sélection des langues
    lang_codes = {
        lang.capitalize(): code for code, lang in googletrans.LANGUAGES.items()
    }
    source_lang = st.sidebar.selectbox(
        "Langue source:",
        sorted(lang_codes.keys()),
        index=sorted(lang_codes.keys()).index("English"),
    )
    target_lang = st.sidebar.selectbox(
        "Langue cible:",
        sorted(lang_codes.keys()),
        index=sorted(lang_codes.keys()).index("French"),
    )

    # Sélection de la police
    st.sidebar.subheader("Style de police")
    font_options = [f"{font['name']} - {font['description']}" for font in BD_FONTS]
    selected_font_idx = st.sidebar.selectbox(
        "Police BD:", range(len(font_options)), format_func=lambda i: font_options[i]
    )
    selected_font = BD_FONTS[selected_font_idx]

    # Options de mise en page
    st.sidebar.subheader("Mise en page")
    page_format = st.sidebar.selectbox(
        "Format de page:", ["A4", "Letter", "Custom Large"]
    )
    font_size = st.sidebar.slider("Taille de police:", 7, 12, 9)
    margins = st.sidebar.slider("Marges (points):", 12, 72, 24)

    # Zone principale - Téléchargement du PDF
    uploaded_file = st.file_uploader("Choisissez un fichier PDF à traduire", type="pdf")

    if uploaded_file is not None:
        # Affichage des informations sur le fichier
        file_details = {
            "Nom du fichier": uploaded_file.name,
            "Type": uploaded_file.type,
            "Taille": f"{uploaded_file.size / 1024:.2f} KB",
        }
        st.write(file_details)

        # Prévisualisation du PDF (première page)
        if st.checkbox("Afficher l'aperçu du PDF original"):
            text_preview = extract_text_from_pdf(uploaded_file)
            st.text_area(
                "Aperçu du texte extrait (500 premiers caractères):",
                text_preview[:500],
                height=150,
            )

        # Téléchargement de la police
        with st.spinner(f"Téléchargement de la police {selected_font['name']}..."):
            font_path = download_bd_font(selected_font)
            bd_font_available = False

            if font_path:
                try:
                    pdfmetrics.registerFont(TTFont("BDFrancaise", font_path))
                    bd_font_available = True
                    st.success(f"Police '{selected_font['name']}' chargée avec succès!")
                except Exception as e:
                    st.error(f"Erreur lors de l'enregistrement de la police: {e}")

        # Bouton pour lancer la traduction
        if st.button("Traduire le document"):
            with st.spinner("Extraction du texte..."):
                # Réinitialiser le curseur de fichier au début
                uploaded_file.seek(0)
                text = extract_text_from_pdf(uploaded_file)
                st.success(f"Texte extrait: {len(text)} caractères")

            with st.spinner(
                f"Traduction en cours de {source_lang} vers {target_lang}..."
            ):
                src_code = lang_codes[source_lang]
                dest_code = lang_codes[target_lang]
                translated_text = translate_text(
                    text, src_lang=src_code, dest_lang=dest_code
                )
                st.success("Traduction terminée!")

                if st.checkbox("Afficher le texte traduit"):
                    st.text_area(
                        "Aperçu de la traduction (500 premiers caractères):",
                        translated_text[:500],
                        height=150,
                    )

            with st.spinner("Création du PDF..."):
                pdf_data = save_text_to_pdf(
                    translated_text,
                    bd_font_available=bd_font_available,
                    font_name="BDFrancaise",
                    page_format=page_format,
                    font_size=font_size,
                    margins=margins,
                )
                st.success("PDF créé avec succès!")

            # Créer un lien de téléchargement
            output_filename = f"traduit_{uploaded_file.name}"
            st.markdown(
                create_download_link(pdf_data, filename=output_filename),
                unsafe_allow_html=True,
            )

            # Bouton de téléchargement via l'API Streamlit
            st.download_button(
                label="📥 Télécharger la traduction",
                data=pdf_data,
                file_name=output_filename,
                mime="application/pdf",
            )


if __name__ == "__main__":
    main()
