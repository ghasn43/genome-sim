import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import random, json, os, io
from PIL import Image

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

def draw_variant_trait_diagram():
    import matplotlib.patches as patches
    fig, ax = plt.subplots(figsize=(6,3))
    ax.axis("off")
    # Boxes
    ax.add_patch(patches.Rectangle((0.05,0.4),0.25,0.2,fill=True,color="#f2f2f2",ec="black"))
    ax.text(0.175,0.5,"Variants\n(Genotype)",ha="center",va="center",fontsize=10)
    ax.add_patch(patches.Rectangle((0.4,0.4),0.25,0.2,fill=True,color="#f2f2f2",ec="black"))
    ax.text(0.525,0.5,"Environment\n(Sun, Diet)",ha="center",va="center",fontsize=10)
    ax.add_patch(patches.Rectangle((0.75,0.4),0.2,0.2,fill=True,color="#ffe6cc",ec="black"))
    ax.text(0.85,0.5,"Trait\n(Skin Tone)",ha="center",va="center",fontsize=10)
    # Arrows
    ax.annotate("", xy=(0.38,0.5), xytext=(0.3,0.5), arrowprops=dict(arrowstyle="->", lw=2))
    ax.annotate("", xy=(0.73,0.5), xytext=(0.65,0.5), arrowprops=dict(arrowstyle="->", lw=2))
    st.pyplot(fig)

def estimate_skin_color_from_photo(uploaded_file):
    image = Image.open(uploaded_file).convert("RGB")
    arr = np.array(image)
    avg_color = arr.mean(axis=(0,1)) / 255.0  # Normalize to 0–1
    return avg_color

# -------------------
# App Title
# -------------------
st.title("🧬 Pigmentation Simulation Studio (Educational)")

mode = st.radio("Choose mode:", [
    "Trait Simulation",
    "Disease Awareness",
    "Custom Variant Editor",
    "Photo Skin Tone Estimator"
])

# -------------------
# Mode 1: Trait Simulation
# -------------------
if mode == "Trait Simulation":
    st.subheader("🧪 Trait Simulation")
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

# -------------------
# Mode 2: Disease Awareness
# -------------------
elif mode == "Disease Awareness":
    st.subheader("🧬 Explore Annotated Variants")
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
    with st.expander("🔎 How variants lead to traits"):
        draw_variant_trait_diagram()

    # Reverse Simulation
    st.subheader("🎚️ Reverse Simulation: Pick a Skin Tone")
    target_score = st.slider("Choose desired pigmentation score", -3, 3, 0)
    sorted_variants = sorted(VISUAL_SCORES.items(), key=lambda x: -abs(x[1]))
    selected = []
    score_sum = 0
    for v, s in sorted_variants:
        if (target_score > 0 and s > 0) or (target_score < 0 and s < 0):
            if abs(score_sum + s) <= abs(target_score):
                selected.append(v)
                score_sum += s
        if score_sum == target_score:
            break
    tone = (target_score + 3) / 6
    color = [tone, tone*0.9, tone*0.8]
    fig, ax = plt.subplots(figsize=(2,2))
    ax.imshow(np.ones((10,10,3)) * color)
    ax.axis("off")
    st.pyplot(fig)
    st.write(f"Suggested variants for score {target_score}: {', '.join(selected) if selected else 'No perfect match'}")
    if st.button("💾 Save this reverse simulation to palette"):
        new_mix = {
            "variants": selected,
            "score": target_score,
            "color": color
        }
        st.session_state.palette.append(new_mix)
        with open(PALETTE_FILE, "w", encoding="utf-8") as f:
            json.dump(st.session_state.palette, f, indent=2)
        st.success(f"✅ Reverse simulation saved into palette as ReverseSim_{len(st.session_state.palette)}!")

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

# -------------------
# Mode 4: Photo Skin Tone Estimator
# -------------------
elif mode == "Photo Skin Tone Estimator":
    st.subheader("📸 Estimate Skin Tone from a Photo (Phenotype)")
    uploaded_file = st.file_uploader("Upload a face or skin photo", type=["jpg","jpeg","png"])
    if uploaded_file:
        avg_color = estimate_skin_color_from_photo(uploaded_file)
        fig, ax = plt.subplots(figsize=(2,2))
        ax.imshow(np.ones((10,10,3))*avg_color)
        ax.axis("off")
        st.pyplot(fig)
        st.write(f"Estimated average skin tone color (normalized RGB): {avg_color}")
        st.info("⚠️ Note: This is only a color estimate. It does NOT reveal DNA variants. For actual variants, lab sequencing is required.")
