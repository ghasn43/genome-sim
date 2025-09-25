import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import random, json, os, io

# -------------------
# Files
# -------------------
PALETTE_FILE = "palette_autosave.json"

# -------------------
# Initialize Palette
# -------------------
if "palette" not in st.session_state:
    if os.path.exists(PALETTE_FILE):
        try:
            with open(PALETTE_FILE, "r", encoding="utf-8") as f:
                st.session_state.palette = json.load(f)
        except Exception:
            st.session_state.palette = []
    else:
        st.session_state.palette = []

# -------------------
# Load Variants
# -------------------
with open("variants.json", "r", encoding="utf-8") as f:
    VARIANT_DB = json.load(f)

VISUAL_SCORES = {
  "SLC24A5_A111T": +2,
  "SLC45A2_F374L": +1,
  "OCA2_R419Q": +1,
  "HERC2_rs12913832": +2,
  "ASIP_rs6058017": +1,
  "KITLG_rs12821256": +1,
  "MC1R_R151C": +1,
  "TYR_W402*": +3,
  "MFSD12_rs10424065": -2,
  "MFSD12_rs112332856": -2,
  "DDB1_rs7948623": -3,
  "SLC24A4_rs12896399": 0,
  "TYRP1_rs13289810": -2,
  "ADAMTS20_rs72755233": -1
}

# -------------------
# Helper Functions
# -------------------
def skin_tone_bar(score):
    fig, ax = plt.subplots(figsize=(5, 1))
    gradient = np.linspace(0, 1, 256).reshape(1, -1)
    ax.imshow(gradient, aspect="auto", cmap="copper")
    ax.set_xticks([0, 128, 255])
    ax.set_xticklabels(["Darker", "Neutral", "Lighter"])
    ax.set_yticks([])
    pos = int((score + 3) / 6 * 255)
    ax.axvline(pos, color="white", linestyle="--", lw=2)
    st.pyplot(fig)

def skin_swatch(before_tone, after_tone, label_before="Baseline", label_after="Variant"):
    fig, ax = plt.subplots(1, 2, figsize=(2, 1))
    ax[0].imshow(np.ones((10,10,3)) * before_tone); ax[0].axis("off"); ax[0].set_title(label_before, fontsize=8)
    ax[1].imshow(np.ones((10,10,3)) * after_tone); ax[1].axis("off"); ax[1].set_title(label_after, fontsize=8)
    st.pyplot(fig)

# -------------------
# App Title
# -------------------
st.title("🧬 Pigmentation Simulation Studio (Educational)")

mode = st.radio("Choose mode:", ["Trait Simulation", "Disease Awareness", "Custom Variant Editor"])

# -------------------
# Mode 1: Trait Simulation
# -------------------
if mode == "Trait Simulation":
    with st.expander("ℹ️ What is Trait Simulation?"):
        st.markdown("""
        Trait Simulation lets you explore what happens when you change a base in a DNA sequence.
        It shows original vs edited codon/protein, and mutation type (silent/missense/nonsense).
        """)

    dna_input = st.text_area("Enter DNA sequence:", value="ATGGAGGAGCCGCAGTCAGATCCTAGCGTCGAGCCCCCT").upper()
    if len(dna_input) % 3 == 0:
        codon_index = st.number_input("Codon index to mutate (0-based):", 0, (len(dna_input)//3)-1, 2)
        new_base = st.text_input("New base (A/T/C/G):", "A")
        if st.button("Simulate Edit"):
            orig_codon = dna_input[codon_index*3:codon_index*3+3]
            edited_dna = list(dna_input)
            edited_dna[codon_index*3] = new_base
            edited_dna = "".join(edited_dna)
            st.write(f"Original Codon: {orig_codon}")
            st.write(f"Edited DNA: {edited_dna}")

            # Allow saving as a custom variant
            if st.button("💾 Save this mutation as custom variant"):
                custom_name = f"CustomVar_{len(st.session_state.palette)+1}"
                effect = "Silent" if orig_codon == edited_dna[codon_index*3:codon_index*3+3] else "Missense"
                score = -1 if effect == "Missense" else 0

                new_variant = {
                    "gene": "CustomGene",
                    "change": f"{orig_codon}>{edited_dna[codon_index*3:codon_index*3+3]}",
                    "effect": effect,
                    "clinical": "User-defined",
                    "condition": "Educational simulation",
                    "flag": "Custom",
                    "source": "User input"
                }

                VARIANT_DB[custom_name] = new_variant
                VISUAL_SCORES[custom_name] = score

                tone = (score + 3) / 6
                st.session_state.palette.append({
                    "variants": [custom_name],
                    "score": score,
                    "color": [tone, tone*0.9, tone*0.8]
                })

                with open(PALETTE_FILE, "w", encoding="utf-8") as f:
                    json.dump(st.session_state.palette, f, indent=2)

                st.success(f"✅ Custom variant saved as {custom_name} and added to palette!")

# -------------------
# Mode 2: Disease Awareness
# -------------------
elif mode == "Disease Awareness":
    with st.expander("ℹ️ What is a Variant?"):
        st.markdown("""
        A genetic variant is a change in DNA compared to a reference.
        Some are benign, some are trait-associated (e.g., skin tone), some pathogenic.
        """)

    choice = st.selectbox("Select a variant:", list(VARIANT_DB.keys()))
    variant = VARIANT_DB[choice]
    st.write(f"**Gene:** {variant['gene']}")
    st.write(f"**Change:** {variant['change']}")
    st.write(f"**Effect:** {variant['effect']}")
    st.write(f"**Condition:** {variant['condition']}")
    st.write(f"**Flag:** {variant['flag']}")

    if choice in VISUAL_SCORES:
        score = VISUAL_SCORES[choice]
        skin_tone_bar(score)
        tone = (score + 3)/6
        skin_swatch([0.5,0.4,0.3], [tone, tone*0.9, tone*0.8])

    # Polygenic Mixing
    st.subheader("🎨 Polygenic Mixing")
    selected_variants = st.multiselect(
        "Select variants to combine:",
        list(VARIANT_DB.keys()),
        default=st.session_state.get("selected_variants", [])
    )
    if selected_variants:
        combined_score = sum(VISUAL_SCORES.get(v,0) for v in selected_variants)
        combined_score = max(-3, min(3, combined_score))
        tone = (combined_score + 3)/6
        after_color = [tone, tone*0.9, tone*0.8]
        skin_swatch([0.5,0.4,0.3], after_color, "Baseline", "Mixed")

        if st.button("💾 Save this mix to palette"):
            st.session_state.palette.append({
                "variants": selected_variants.copy(),
                "score": combined_score,
                "color": after_color
            })
            with open(PALETTE_FILE, "w", encoding="utf-8") as f:
                json.dump(st.session_state.palette, f, indent=2)

# -------------------
# Mode 3: Custom Variant Editor
# -------------------
elif mode == "Custom Variant Editor":
    st.subheader("🛠️ Create Your Own Variant")

    with st.form("custom_variant_form"):
        custom_name = st.text_input("Variant name", value=f"CustomVar_{len(st.session_state.palette)+1}")
        gene_name = st.text_input("Gene name", value="CustomGene")
        dna_change = st.text_input("DNA/Protein change", value="c.123A>T (p.Lys41Asn)")
        effect = st.selectbox("Effect type", ["Silent", "Missense", "Nonsense", "Regulatory"])
        clinical = st.text_input("Clinical significance", value="User-defined")
        condition = st.text_area("Condition / Notes", value="Educational simulation")
        score = st.slider("Pigmentation score (darker -3 ←→ lighter +3)", -3, 3, 0)
        submit = st.form_submit_button("💾 Save Custom Variant")

    if submit:
        new_variant = {
            "gene": gene_name,
            "change": dna_change,
            "effect": effect,
            "clinical": clinical,
            "condition": condition,
            "flag": "Custom",
            "source": "User input"
        }

        VARIANT_DB[custom_name] = new_variant
        VISUAL_SCORES[custom_name] = score

        tone = (score + 3) / 6
        st.session_state.palette.append({
            "variants": [custom_name],
            "score": score,
            "color": [tone, tone*0.9, tone*0.8]
        })

        with open(PALETTE_FILE, "w", encoding="utf-8") as f:
            json.dump(st.session_state.palette, f, indent=2)

        st.success(f"✅ Custom variant '{custom_name}' saved and added to palette!")
