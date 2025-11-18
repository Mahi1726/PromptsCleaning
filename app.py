# streamlit_add_sno_app.py
import re
import streamlit as st

st.set_page_config(page_title="SNo Adder — Prompt Formatter", layout="wide")
st.title("SNo Adder — Move Part number after URL (no space)")
st.markdown(
    """
Paste your multi-part prompts (the "Part X: ..." list). This tool will:

- Extract each `Part N:` block.
- For each part, add the serial number (SNo) **on a new line after the URL with no space**, or **at the start** if there's no URL. Example:
  - With URL: `https://...&hm=...\n1Ultra realistic...`
  - No URL: `1Ultra realistic...`
"""
)

st.sidebar.header("Options")
start_index = st.sidebar.number_input("Start numbering from", min_value=1, value=1, step=1)

# Session-backed text area so example loading works reliably
if 'input_text' not in st.session_state:
    st.session_state['input_text'] = ''

input_text = st.text_area(
    "Paste your full prompt text here (keep the original 'Part X:' markers)",
    value=st.session_state['input_text'],
    height=400,
    key='main_text_area'
)

col1, col2 = st.columns([1, 1])
with col1:
    if st.button("Process and Preview"):
        st.session_state['last_action'] = 'process'
with col2:
    if st.button("Load example (small)"):
        example = (
            "Part 1: https://cdn.discordapp.com/example1.jpg?abc Example prompt one\n"
            "Part 2: Example prompt without url\n"
            "Part 3: https://cdn.discordapp.com/example3.png More text after URL\n"
        )
        st.session_state['input_text'] = example
        st.experimental_rerun()

# If user clicked process (or there's prefilled text), handle processing
if st.session_state.get('last_action') == 'process' or input_text.strip():
    text_to_process = input_text if input_text.strip() else st.session_state.get('input_text', '')
    if not text_to_process.strip():
        st.warning("No input found. Paste your prompt list or load the example.")
    else:
        # Find parts using regex; fallback to lines if no 'Part' markers
        pattern = re.compile(r"Part\s*(\d+)\s*:\s*(.*?)(?=(?:\nPart\s*\d+\s*:)|\Z)", re.S | re.I)
        matches = list(pattern.finditer(text_to_process))

        if matches:
            parts = []
            for m in matches:
                num = int(m.group(1))
                content = m.group(2).strip()
                parts.append((num, content))
        else:
            # fallback: each non-empty line becomes a 'part' with incrementing number
            lines = [ln for ln in text_to_process.splitlines() if ln.strip()]
            parts = []
            for i, ln in enumerate(lines, start=start_index):
                parts.append((i, ln.strip()))

        st.write(f"Detected {len(parts)} part(s). Starting SNo at {start_index}.")

        output_lines = []
        for idx_offset, (original_num, content) in enumerate(parts, start=0):
            idx = start_index + idx_offset
            # Find first URL (http or https)
            url_match = re.search(r"https?://\S+", content)
            if url_match:
                url = url_match.group(0)
                prefix = content[:url_match.start()]
                suffix = content[url_match.end():].lstrip()
                # Keep URL on its own line, then put the number immediately followed by prompt text on next line
                new_content = prefix + url + "\n" + f"{idx}" + suffix
            else:
                # No URL: prefix number directly at start (no space)
                new_content = f"{idx}{content}"
            output_lines.append(new_content)

        result = "\n\n".join(output_lines)

        st.subheader("Preview")
        st.code(result, language="text")

        # Provide a copy area and a download button
        st.markdown("**Options**")
        st.text_area("Formatted output (copy from here):", value=result, height=300)

        # Download as bytes
        data_bytes = result.encode('utf-8')
        st.download_button("Download formatted prompts (.txt)", data=data_bytes, file_name="formatted_prompts.txt", mime="text/plain")

        # Quick validation to detect accidental URL modifications like '&65' appended at end
        broken_urls = []
        for line in result.splitlines():
            if line.strip().startswith('http') and re.search(r"\?[^\s]*\d{1,3}$", line):
                broken_urls.append(line.strip())
        if broken_urls:
            st.error("Warning: detected URLs that appear to have a number appended to the query string. Please check these:")
            for u in broken_urls:
                st.code(u)

st.markdown("---")
st.caption("Number will be placed on its own line immediately after the URL (no space before prompt text).")
