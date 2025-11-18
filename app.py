import re
import streamlit as st
from io import StringIO

st.set_page_config(page_title="SNo Adder — Prompt Formatter", layout="wide")
st.title("SNo Adder — Move Part number after URL (no space)")
st.markdown(
    """
Paste your multi-part prompts (the "Part X: ..." list). This tool will:

- Extract each `Part N:` block.
- For each part, add the serial number (SNo) **directly after the URL with no space**, or **at the start** if there's no URL. Example:
  - With URL: `https://...&hm=...& 1Ultra realistic...`
  - No URL: `1Ultra realistic...`

Options are provided to start numbering from a different number and to preview results before downloading.
"""
)

st.sidebar.header("Options")
start_index = st.sidebar.number_input("Start numbering from", min_value=1, value=1, step=1)

input_text = st.text_area("Paste your full prompt text here (keep the original 'Part X:' markers)", height=400)

if st.button("Process and Preview"):
    if not input_text.strip():
        st.warning("Paste your prompt list first.")
    else:
        # Regex to capture blocks like "Part 12: <content>" (greedy until next Part or end)
        pattern = re.compile(r"Part\s*\d+\s*:\s*(.*?)(?=(?:\nPart\s*\d+\s*:)|\Z)", re.S | re.I)
        parts = pattern.findall(input_text)
        if not parts:
            # If no Part markers found, try splitting by lines and treat each non-empty line as a part
            st.info("No 'Part X:' markers found — falling back to line-by-line processing.")
            raw_lines = [ln for ln in input_text.splitlines() if ln.strip()]
            parts = raw_lines
        
        output_lines = []
        for idx, content in enumerate(parts, start=start_index):
            content = content.strip()
            # Find first URL (http or https)
            url_match = re.search(r"https?://\S+", content)
            if url_match:
                url = url_match.group(0)
                # Keep the URL intact, put the serial number on the next line with NO space before the prompt text
                prefix = content[:url_match.start()]
                suffix = content[url_match.end():].lstrip()  # remove leading spaces so number joins directly to prompt text
                new_content = prefix + url + "\\n" + f"{idx}" + suffix
