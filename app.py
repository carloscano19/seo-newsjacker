import streamlit as st
import feedparser
import pandas as pd
import anthropic
from datetime import datetime
import io

# --- 1. CONFIGURACIÓN DE PÁGINA (ESTILO PRO) ---
st.set_page_config(
    page_title="SEO Newsjacker Pro",
    page_icon="🚀",
    layout="wide"
)

# --- 2. CABECERA PROFESIONAL ---
st.title("🚀 SEO Newsjacker Pro")
st.markdown("### Your AI-Powered Content Strategy Platform")
st.markdown("Track competitor trends, generate viral article titles, and create comprehensive content briefs - all powered by Claude AI.")
st.divider()

# --- 3. SIDEBAR (CONFIGURACIÓN) ---
with st.sidebar:
    st.header("⚙️ Settings")
    
    with st.expander("🔑 API Configuration", expanded=True):
        api_key = st.text_input("Anthropic API Key", type="password")
        
    with st.expander("📡 RSS Feed Sources", expanded=True):
        default_feeds = """https://www.coindesk.com/arc/outboundfeeds/rss/
https://cointelegraph.com/rss
https://beincrypto.com/feed/
https://decrypt.co/feed
https://bitcoinmagazine.com/feed"""
        rss_urls = st.text_area("Feeds (One per line)", value=default_feeds, height=150).split('\n')

    st.markdown("---")
    st.info("Status: Ready to Monitor")

# --- 4. FUNCIONES DEL BACKEND ---
def fetch_rss_data(urls):
    all_news = []
    for url in urls:
        if url.strip():
            feed = feedparser.parse(url)
            for entry in feed.entries[:3]: 
                all_news.append({
                    'Source': feed.feed.get('title', 'Unknown'),
                    'Title': entry.title,
                    'Published': entry.get('published', 'No date'),
                    'Link': entry.link
                })
    return pd.DataFrame(all_news)

# --- 5. INITIALIZE SESSION STATE (MEMORIA) ---
if 'generated_titles' not in st.session_state:
    st.session_state.generated_titles = []
if 'content_brief' not in st.session_state:
    st.session_state.content_brief = ""

# --- 6. INTERFAZ PRINCIPAL ---

# A) TABLA DE NOTICIAS
st.subheader("📰 Global Crypto News Feed")
st.caption("Real-time headlines from top crypto news sources")

if api_key:
    client = anthropic.Anthropic(api_key=api_key)
    
    # Cargar noticias
    df = fetch_rss_data(rss_urls)
    
  # 1. GESTIÓN DE ESTADO (MEMORIA)
    if 'editor_key' not in st.session_state:
        st.session_state.editor_key = 0
    if 'default_selection' not in st.session_state:
        st.session_state.default_selection = False

    # 2. BOTONES MÁGICOS (Con recarga forzada)
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("✅ All"):
            st.session_state.default_selection = True
            st.session_state.editor_key += 1
            st.rerun()
    with col2:
        if st.button("❌ None"):
            st.session_state.default_selection = False
            st.session_state.editor_key += 1
            st.rerun()

    # 3. PREPARAR DATOS
    if 'Select' not in df.columns:
        df.insert(0, "Select", st.session_state.default_selection)
    else:
        df['Select'] = st.session_state.default_selection

    # 4. MOSTRAR TABLA EDITABLE (Con clave dinámica)
    st.info("👇 Select the news items you want to analyze:")
    
    edited_df = st.data_editor(
        df,
        column_config={
            "Select": st.column_config.CheckboxColumn(
                "Analyze?",
                help="Select to include in AI analysis",
                default=False,
            ),
            "Link": st.column_config.LinkColumn("Link")
        },
        disabled=["Source", "Title", "Published"],
        hide_index=True,
        use_container_width=True,
        height=400,
        key=f"editor_{st.session_state.editor_key}"
    )
    
    # FILTRAR SOLO LAS ELEGIDAS
    selected_news = edited_df[edited_df["Select"] == True]
    
    st.divider()

    # B) GENERADOR DE TÍTULOS VIRALES
    st.subheader("✨ AI Trend Hunter")
    st.caption("Generate crypto-focused viral article titles based on current headlines")
    if st.button("🚀 Analyze Trends & Generate Viral Titles", type="primary"):
    with st.spinner("Reading news, filtering noise, and brainstorming viral angles..."):
        
        # 1. VERIFICAR SELECCIÓN
        if selected_news.empty:
            st.error("⚠️ Selecciona al menos una noticia de la tabla para analizar.")
            st.stop()

        # 2. PREPARAR TEXTO (USANDO SOLO LAS NOTICIAS MARCADAS)
        headlines_text = "\n".join([f"- {row['Title']} ({row['Source']})" for index, row in selected_news.iterrows()])

        # 3. EL PROMPT (CON LAS REGLAS ANTIALUCINACIONES 🚫👻)
        prompt = f"""
        You are the Editor of 'Fantokens.com'.
        Read these headlines from the crypto market:
        {headlines_text}

        Generate 10 Viral Article Titles based STRICTLY on the provided headlines.

        CRITICAL RULES:
        1. **STRICT SOURCE ADHERENCE**: You must ONLY use the topics, companies, coins, and events mentioned in the text above. 
        2. **NO HALLUCINATIONS**: Do NOT bring in outside general topics (like generic 'Bitcoin rises', 'DeFi trends', or 'Ethereum updates') unless they are explicitly in the source text.
        3. **DEEP DIVE**: If only one news item is provided, you MUST generate 10 different viral angles for that SINGLE story.
           - Use different hooks: Fear, FOMO, Technology, Financial Impact, Quotes, Future Prediction.
        4. Every title MUST be catchy, punchy, and click-worthy.

        Return ONLY the clean list of 10 titles (no intro text).
        """

        # 4. LLAMADA A LA API (CLAUDE HAIKU)
        message = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )

        # 5. GUARDAR RESULTADOS
        raw_text = message.content[0].text
        st.session_state.generated_titles = [line.strip() for line in raw_text.split('\n') if line.strip()]
    # MOSTRAR TÍTULOS (DISEÑO 2 COLUMNAS)
    if st.session_state.generated_titles:
        st.success("✅ Viral Angles Detected!")
        
        col1, col2 = st.columns(2)
        
        # Dividir lista en dos
        mid_point = (len(st.session_state.generated_titles) + 1) // 2
        left_titles = st.session_state.generated_titles[:mid_point]
        right_titles = st.session_state.generated_titles[mid_point:]
        
        with col1:
            for t in left_titles:
                st.markdown(f"**• {t}**")
        with col2:
            for t in right_titles:
                st.markdown(f"**• {t}**")
        
        st.divider()

        # C) GENERADOR DE BRIEFS
        st.subheader("📝 Content Brief Generator")
        st.caption("Select a winning title to generate a full SEO brief for your writers")
        
        selected_title = st.selectbox("Choose a title to generate a content brief:", st.session_state.generated_titles)
        
        if st.button("📄 Generate Detailed Brief"):
            with st.spinner(f"Writing strategy for: {selected_title}..."):
                brief_prompt = f"""
                Create a Content Brief for the article title: '{selected_title}'.
                
                Follow this EXACT template structure:
                
                Post Objective
                [Explain the goal]
                
                Target Audience
                [Primary and Secondary]
                
                Tone
                [Educational/Technical but accessible]
                
                Article Structure
                [Provide a vertical list of bullet points for the headers]
                
                Keywords with Estimated Intent
                [List 4-5 keywords]
                
                LLM Optimization Notes
                [Include analogies like "liquidity = water flow"]
                
                IMPORTANT: Use BOLD text for key terms. No financial advice.
                """
                
                message_brief = client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=2000,
                    messages=[{"role": "user", "content": brief_prompt}]
                )
                
                st.session_state.content_brief = message_brief.content[0].text
        
        # MOSTRAR Y DESCARGAR BRIEF
        if st.session_state.content_brief:
            with st.container(border=True):
                st.markdown(st.session_state.content_brief)
                
                st.download_button(
                    label="📥 Download Brief (Markdown)",
                    data=st.session_state.content_brief,
                    file_name="seo_content_brief.md",
                    mime="text/markdown",
                    use_container_width=True
                )

else:
    st.warning("👈 Please enter your Anthropic API Key in the sidebar to start.")
