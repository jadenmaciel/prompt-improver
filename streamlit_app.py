import streamlit as st
from app import PromptAnalyzer, PromptBuilder

st.set_page_config(page_title="Prompt Improver", layout="wide")

st.markdown("""
<style>
/* Custom styling for a more modern look */
.stTextArea textarea {
    font-family: monospace;
}
</style>
""", unsafe_allow_html=True)

st.title("✦ Prompt Improver")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### YOUR PROMPT")
    raw_prompt = st.text_area("Enter prompt here", height=400, label_visibility="collapsed", placeholder="Type or paste your raw prompt here...")
    
    st.markdown("### OPTIONS")
    c1, c2 = st.columns(2)
    model = c1.text_input("Model", placeholder="Claude, GPT-4...")
    audience = c2.text_input("Audience", placeholder="junior dev, non-technical...")
    
    c3, c4 = st.columns(2)
    output_fmt = c3.text_input("Format", placeholder="bullets, JSON, table...")
    tone = c4.text_input("Tone", placeholder="concise, step-by-step...")

    if st.button("Improve Prompt ✦", type="primary", use_container_width=True):
        if not raw_prompt.strip():
            st.warning("Please enter a prompt first.")
        else:
            analyzer = PromptAnalyzer()
            builder = PromptBuilder()
            
            # Reusing the exact AI logic extracted from app.py
            analysis = analyzer.analyze(raw_prompt)
            meta = {
                "model": model,
                "audience": audience,
                "output_fmt": output_fmt,
                "tone": tone
            }
            
            result = builder.build(raw_prompt, analysis, meta)
            st.session_state.result = result
            st.session_state.analysis = analysis

with col2:
    st.markdown("### IMPROVED PROMPT")
    if "result" in st.session_state:
        st.code(st.session_state.result, language="markdown")
        
        st.divider()
        st.markdown("### ANALYSIS")
        analysis = st.session_state.analysis
        
        badges = []
        if analysis.get('has_role'): badges.append("✅ Role")
        if analysis.get('has_context'): badges.append("✅ Context")
        if analysis.get('has_task'): badges.append("✅ Task")
        if analysis.get('has_output_format'): badges.append("✅ Format")
        if analysis.get('has_constraints'): badges.append("✅ Constraints")
        
        st.write(" | ".join(badges) if badges else "No elements detected.")
    else:
        st.info("Your improved prompt will appear here.")
