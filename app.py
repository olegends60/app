import io
import numpy as np
import streamlit as st
import librosa
import librosa.display
import matplotlib.pyplot as plt

st.set_page_config(page_title="Tono Norteño", page_icon="🎵", layout="centered")

NOTE_NAMES = ["DO", "DO♯/RE♭", "RE", "RE♯/MI♭", "MI", "FA",
              "FA♯/SOL♭", "SOL", "SOL♯/LA♭", "LA", "LA♯/SI♭", "SI"]
MAJOR_PROFILE = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09,
                          2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
MINOR_PROFILE = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53,
                          2.54, 4.75, 3.98, 2.69, 3.34, 3.17])

TRIADS = {
    "mayor": [0, 4, 7],
    "menor": [0, 3, 7],
    "disminuido": [0, 3, 6],
}

def corr(a, b):
    if np.std(a) < 1e-8 or np.std(b) < 1e-8:
        return 0.0
    return float(np.corrcoef(a, b)[0, 1])

def detect_key(chroma):
    profile = np.mean(chroma, axis=1)
    profile = (profile - profile.mean()) / (profile.std() + 1e-9)
    candidates = []
    for root in range(12):
        major = np.roll(MAJOR_PROFILE, root)
        minor = np.roll(MINOR_PROFILE, root)
        candidates.append((corr(profile, major), root, "mayor"))
        candidates.append((corr(profile, minor), root, "menor"))
    candidates.sort(reverse=True)
    best = candidates[0]
    confidence_gap = best[0] - candidates[1][0]
    return NOTE_NAMES[best[1]], best[2], max(0.0, min(1.0, (best[0] + 1) / 2)), confidence_gap

def chord_templates():
    names, templates = [], []
    for root in range(12):
        for quality, intervals in TRIADS.items():
            v = np.zeros(12)
            for i in intervals:
                v[(root + i) % 12] = 1.0
            names.append(f"{NOTE_NAMES[root]} {quality}")
            templates.append(v)
    return names, np.array(templates)

CHORD_NAMES, CHORD_TEMPLATES = chord_templates()

def detect_chords(chroma, sr, hop_length, segment_seconds=2.0):
    # Average chroma in short windows, then compare to simple major/minor/diminished templates.
    frames_per_segment = max(1, int(segment_seconds * sr / hop_length))
    results = []
    for start in range(0, chroma.shape[1], frames_per_segment):
        end = min(chroma.shape[1], start + frames_per_segment)
        vec = np.mean(chroma[:, start:end], axis=1)
        norm = np.linalg.norm(vec)
        if norm < 1e-8:
            continue
        vec = vec / norm
        template_norms = CHORD_TEMPLATES / (np.linalg.norm(CHORD_TEMPLATES, axis=1, keepdims=True) + 1e-9)
        scores = template_norms @ vec
        best = int(np.argmax(scores))
        time_start = start * hop_length / sr
        time_end = end * hop_length / sr
        results.append({
            "inicio": time_start,
            "fin": time_end,
            "acorde": CHORD_NAMES[best],
            "puntuacion": float(scores[best])
        })
    # Merge adjacent identical labels.
    merged = []
    for item in results:
        if merged and merged[-1]["acorde"] == item["acorde"]:
            merged[-1]["fin"] = item["fin"]
            merged[-1]["puntuacion"] = (merged[-1]["puntuacion"] + item["puntuacion"]) / 2
        else:
            merged.append(item.copy())
    return merged

def analyze_audio(data, filename="audio"):
    y, sr = librosa.load(io.BytesIO(data), sr=22050, mono=True, duration=300)
    if len(y) < sr * 3:
        raise ValueError("El audio debe durar al menos 3 segundos.")
    y, _ = librosa.effects.trim(y, top_db=35)
    if len(y) < sr * 3:
        raise ValueError("No se detectó suficiente audio útil. Prueba con una grabación más larga.")
    hop = 512
    chroma = librosa.feature.chroma_stft(y=y, sr=sr, hop_length=hop)
    key, mode, confidence, gap = detect_key(chroma)
    chords = detect_chords(chroma, sr, hop)
    duration = len(y) / sr
    return {
        "key": key, "mode": mode, "confidence": confidence, "gap": gap,
        "chords": chords, "duration": duration, "sr": sr, "y": y, "chroma": chroma
    }

st.title("🎵 Tono Norteño")
st.caption("Analizador musical experimental para músicos norteños")
st.write("Sube una grabación para estimar la tonalidad y una secuencia inicial de acordes. El resultado es orientativo: las mezclas con acordeón, bajo, tuba y batería pueden confundir al detector.")

uploaded = st.file_uploader("Elige un archivo de audio", type=["mp3", "wav", "m4a", "ogg", "flac"])
mic_enabled = st.toggle("También quiero grabar con el micrófono", value=False)
if mic_enabled:
    st.info("En esta versión web gratuita, usa el grabador de tu teléfono para guardar un audio y súbelo aquí. La captura directa desde el micrófono se añadirá en la siguiente iteración.")

if uploaded:
    st.audio(uploaded)
    if st.button("Analizar canción", type="primary", use_container_width=True):
        try:
            with st.spinner("Escuchando y analizando armonía…"):
                result = analyze_audio(uploaded.getvalue(), uploaded.name)
            st.session_state["analysis"] = result
            st.success("Análisis terminado.")
        except Exception as e:
            st.error(f"No se pudo analizar el archivo: {e}")

if "analysis" in st.session_state:
    result = st.session_state["analysis"]
    st.divider()
    st.subheader("Resultado")
    c1, c2 = st.columns(2)
    c1.metric("Tono estimado", f'{result["key"]} {result["mode"]}')
    c2.metric("Duración analizada", f'{int(result["duration"] // 60)}:{int(result["duration"] % 60):02d}')
    st.caption("Confianza orientativa del perfil tonal: " + ("alta" if result["confidence"] > 0.72 else "media" if result["confidence"] > 0.60 else "baja") + ". No es una probabilidad calibrada.")
    st.subheader("Progresión armónica estimada")
    st.write(" → ".join(x["acorde"] for x in result["chords"]) or "No se detectaron acordes.")
    st.caption("Cada acorde representa un tramo aproximado; los cambios reales pueden ocurrir antes o después.")
    rows = []
    for ch in result["chords"]:
        rows.append({
            "Inicio": f'{int(ch["inicio"] // 60):02d}:{ch["inicio"] % 60:05.2f}',
            "Fin": f'{int(ch["fin"] // 60):02d}:{ch["fin"] % 60:05.2f}',
            "Acorde estimado": ch["acorde"],
            "Puntaje de coincidencia": f'{ch["puntuacion"]:.2f}'
        })
    st.dataframe(rows, use_container_width=True, hide_index=True)
    st.subheader("Mapa de notas (cromagrama)")
    fig, ax = plt.subplots(figsize=(10, 3.5))
    img = librosa.display.specshow(result["chroma"], x_axis="time", y_axis="chroma",
                                   sr=result["sr"], hop_length=512, ax=ax)
    ax.set_title("Energía aproximada de las 12 notas")
    fig.colorbar(img, ax=ax, format="%+2.0f")
    st.pyplot(fig)
    st.caption("Versión inicial: detecta la tonalidad mediante perfiles de notas y compara ventanas de audio con plantillas de tríadas. No separa instrumentos ni reemplaza una transcripción musical profesional.")
