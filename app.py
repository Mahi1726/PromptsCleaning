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
                # Build new URL with number directly appended (no space)
                new_url = f"{url}{idx}"
                # Replace only the first occurrence
                new_content = content[:url_match.start()] + new_url + content[url_match.end():]
            else:
                # No URL: prefix number directly at start (no space)
                new_content = f"{idx}{content}"
            output_lines.append(new_content)

        result = "\n\n".join(output_lines)
        st.subheader("Preview")
        st.code(result, language="text")

        # Allow download
        buf = StringIO()
        buf.write(result)
        buf.seek(0)
        st.download_button("Download formatted prompts (.txt)", data=buf, file_name="formatted_prompts.txt", mime="text/plain")

# Helpful example button
if st.button("Load example (small)"):
    example = (
        "Part 1: https://cdn.discordapp.com/example1.jpg?abc Example prompt one\n"
        "Part 2: Example prompt without url\n"
        "Part 3: https://cdn.discordapp.com/example3.png More text after URL\n"
    )
    st.experimental_set_query_params()  # no-op to give user feedback
    st.session_state['example_loaded'] = True
    st.write("Example loaded below — click Process and Preview")
    st.text_area("Paste your full prompt text here (the 'Part X:' list)", value=example, height=200)

st.markdown("---")
st.caption("Built to add the serial number (SNo) exactly as requested: number appended with NO SPACE after URL or at the very start when no URL exists.")
