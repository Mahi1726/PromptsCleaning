import re
import streamlit as st

st.set_page_config(page_title="SNo Adder — Prompt Formatter", layout="wide")
st.title("SNo Adder — Move Part number after URL (no space)")
st.markdown(
    """
Paste your multi-part prompts (the "Part X:" list) or mixed-format prompts. This tool will:

- Detect `Part N:` blocks, numbered lines like `1Warm...`, or blank-line-separated blocks.
- For each block, place the serial number (SNo) **on a new line immediately after any URL** (no space before prompt text), or **at the start** if no URL is present.

Example with URL (Option A behavior):

If a block already starts with a number (e.g. `5Warm...`) the app preserves it by default; enable "Force renumbering" to overwrite.
"""
)

st.sidebar.header("Options")
start_index = st.sidebar.number_input("Start numbering from", min_value=1, value=1, step=1)
force_renumber = st.sidebar.checkbox("Force renumbering (ignore existing leading numbers)", value=False)

# Keep input across reruns
if 'input_text' not in st.session_state:
    st.session_state['input_text'] = ''

input_text = st.text_area(
    "Paste your full prompt text here (any format)",
    value=st.session_state['input_text'],
    height=520,
    key='main_text_area'
)

col1, col2 = st.columns([1, 1])
with col1:
    if st.button("Process and Preview"):
        st.session_state['last_action'] = 'process'
with col2:
    if st.button("Load example (small)"):
        st.session_state['input_text'] = (
            "Part 1: https://cdn.discordapp.com/example1.jpg?abc Example prompt one\n"
            "Part 2: Example prompt without url\n"
            "Part 3: https://cdn.discordapp.com/example3.png More text after URL\n"
        )
        st.experimental_rerun()


def split_into_candidate_blocks(text):
    # Prefer explicit Part N: groups first
    part_pattern = re.compile(r"Part\s*(\d+)\s*:\s*(.*?)(?=(?:\nPart\s*\d+\s*:)|\Z)", re.S | re.I)
    matches = list(part_pattern.finditer(text))
    if matches:
        return [m.group(2).strip() for m in matches]

    # Fallback: split on two-or-more newlines into blocks
    blocks = [b.strip() for b in re.split(r"\n\s*\n+", text) if b.strip()]
    if blocks:
        return blocks

    # Last fallback: treat each non-empty line as a block
    return [ln.strip() for ln in text.splitlines() if ln.strip()]


def extract_leading_number(block):
    # If block starts with digits (like '5Warm...' or '5 Warm...'), capture them
    m = re.match(r"^(\d+)\s*(.*)$", block)
    if m:
        return int(m.group(1)), m.group(2).lstrip()
    # Also handle digits glued to word: '5Warm...'
    m2 = re.match(r"^(\d+)(\S.*)$", block)
    if m2:
        return int(m2.group(1)), m2.group(2).lstrip()
    return None, block


if st.session_state.get('last_action') == 'process' or input_text.strip():
    text_to_process = input_text if input_text.strip() else st.session_state.get('input_text', '')
    if not text_to_process.strip():
        st.warning("No input found. Paste your prompt list or load the example.")
    else:
        blocks = split_into_candidate_blocks(text_to_process)
        st.write(f"Found {len(blocks)} block(s) to process")

        output_blocks = []
        renumber_idx = start_index
        for b in blocks:
            # Detect existing leading number if any
            leading_num, rest = extract_leading_number(b)

            if leading_num is not None and not force_renumber:
                used_num = leading_num
                content_without_leading_num = rest
            else:
                used_num = renumber_idx
                content_without_leading_num = b

            # Find first URL in content_without_leading_num
            url_match = re.search(r"https?://\S+", content_without_leading_num)
            if url_match:
                url = url_match.group(0)
                prefix = content_without_leading_num[:url_match.start()]
                suffix = content_without_leading_num[url_match.end():].lstrip()
                # Keep URL intact; put SNo on the next line, immediately followed by prompt text (no space)
                new_block = prefix + url + "\n" + f"{used_num}" + suffix
            else:
                # No URL: prefix number directly at start (no space)
                new_block = f"{used_num}{content_without_leading_num}"

            output_blocks.append(new_block)

            # Increment renumber index only when we generated the number (or force_renumber)
            if force_renumber or leading_num is None:
                renumber_idx += 1

        result = "\n\n".join(output_blocks)

        st.subheader("Preview")
        st.code(result, language="text")

        st.markdown("**Formatted output (copy from here):**")
        st.text_area("", value=result, height=420)

        # Download as bytes to avoid Streamlit APIException about binary format
        st.download_button(
            "Download formatted prompts (.txt)",
            data=result.encode('utf-8'),
            file_name="formatted_prompts.txt",
            mime="text/plain"
        )

        # Quick safety check: detect accidental URL mutations like '&65' appended
        broken = []
        for line in result.splitlines():
            if line.strip().startswith('http') and re.search(r"\?[^\"]*\d{1,3}$", line):
                broken.append(line.strip())
        if broken:
            st.error("Detected URLs that look like they had numbers appended to the query string — review these:")
            for u in broken:
                st.code(u)

st.markdown("---")
st.caption(
    "If nothing changes when you click 'Process and Preview', try pasting a small sample (3–6 lines) and press the button — or click 'Load example (small)'. "
    "If it still does nothing, tell me exactly what you clicked and whether any errors appear in your terminal/logs."
)
