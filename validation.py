import pandas as pd
from jiwer import wer

from datetime import datetime
import json

def tiempo_a_segundos(tiempo_str):
    t = datetime.strptime(tiempo_str, "%M:%S")
    return t.minute * 60 + t.second

def calcular_desfase(llm, real, umbral=5):
    desfases = []
    dentro_de_umbral = 0

    longitud = min(len(llm), len(real))

    for idx in range(longitud):
        fase_llm = llm[idx]
        fase_real = real[idx]

        t_llm = tiempo_a_segundos(fase_llm["inicio"])
        t_real = tiempo_a_segundos(fase_real["inicio"])
        desfase = abs(t_llm - t_real)

        desfases.append(desfase)
        if desfase <= umbral:
            dentro_de_umbral += 1

    offset_medio = sum(desfases) / longitud
    porcentaje_ok = dentro_de_umbral / longitud
    return offset_medio, porcentaje_ok


def validate_transcription_pair(pipeline_csv_path, real_csv_path):
    """
    Valida una transcripción generada (pipeline) frente a una referencia manual (real),
    devolviendo el WER y la precisión de diarización basada en solapamiento temporal.
    """

    # Cargar archivos
    try:
        pipeline_df = pd.read_csv(pipeline_csv_path)
        real_df = pd.read_csv(real_csv_path)
    except Exception as e:
        print(f"❌ Error loading CSV files: {e}")
        return None

    # --- Cálculo del WER ---
    pipeline_text = " ".join(pipeline_df["transcription"].astype(str).str.lower())
    real_text = " ".join(real_df["transcription"].astype(str).str.lower())
    try:
        word_error_rate = wer(real_text, pipeline_text)
    except Exception as e:
        print(f"❌ Error computing WER: {e}")
        word_error_rate = None

    # --- Cálculo de precisión de hablantes ---
    correct = 0
    total = 0

    for _, row in pipeline_df.iterrows():
        start_p, end_p, speaker_p = row["start"], row["end"], row["speaker"]

        # Buscar segmento en real que se solape
        overlaps = real_df[
            (real_df["start"] < end_p) & (real_df["end"] > start_p)
        ]

        if not overlaps.empty:
            matched = overlaps.iloc[0]
            speaker_r = matched["speaker"]
            if speaker_p == speaker_r:
                correct += 1
            total += 1

    diarization_accuracy = correct / total if total > 0 else None

    return {
        "pipeline_file": pipeline_csv_path,
        "reference_file": real_csv_path,
        "WER": word_error_rate,
        "Diarization_Accuracy": diarization_accuracy,
        "Total_Matched_Segments": total
    }
if __name__ == "__main__":

    # ---------- Validación de transcripción ----------
    print("🔎 VALIDACIÓN")
    file_pairs = [
        ("Results/Caso1_InfeccionRespiratoria/audio_cleaned_text_and_roles.csv", "Validation/Caso1_InfeccionRespiratoria/audio_cleaned_text_and_roles.csv"),
        ("Results/Caso2_Lunares/audio_cleaned_text_and_roles.csv", "Validation/Caso2_Lunares/audio_cleaned_text_and_roles.csv"),
        ("Results/Caso3_Quemaduras/audio_cleaned_text_and_roles.csv", "Validation/Caso3_Quemaduras/audio_cleaned_text_and_roles.csv"),
    ]
    results = []

    for pipeline_csv, real_csv in file_pairs:
        res = validate_transcription_pair(pipeline_csv, real_csv)
        if res:
            results.append(res)

    if results:
        wer_list = [r["WER"] for r in results if r["WER"] is not None]
        diar_list = [r["Diarization_Accuracy"] for r in results if r["Diarization_Accuracy"] is not None]
        avg_wer = sum(wer_list) / len(wer_list) if wer_list else None
        avg_diar = sum(diar_list) / len(diar_list) if diar_list else None

        print("\n📈 MÉTRICAS GLOBALES TRANSCRIPCIÓN:")
        if avg_wer is not None:
            print(f"   Average WER: {avg_wer:.2%}")
        if avg_diar is not None:
            print(f"   Average Diarization Accuracy: {avg_diar:.2%}")
    else:
        print("❌ No se pudo validar ningún archivo de transcripción.")

    # ---------- Validación de segmentación de fases ----------
    pares = [
        ("Results/Caso1_InfeccionRespiratoria/audio_clinic_segmentation.json", "Validation/Caso1_InfeccionRespiratoria/audio_clinic_segmentation.json"),
        ("Results/Caso2_Lunares/audio_clinic_segmentation.json", "Validation/Caso2_Lunares/audio_clinic_segmentation.json"),
        ("Results/Caso3_Quemaduras/audio_clinic_segmentation.json", "Validation/Caso3_Quemaduras/audio_clinic_segmentation.json"),
    ]

    total_offset = 0
    total_porcentaje = 0
    n = 0

    for i, (ruta_llm, ruta_real) in enumerate(pares):
        try:
            with open(ruta_llm, "r", encoding="utf-8") as f1:
                llm_data = json.load(f1)["timeline_visual"]["estructura"]
            with open(ruta_real, "r", encoding="utf-8") as f2:
                real_data = json.load(f2)["timeline_visual"]["estructura"]

            offset, porcentaje = calcular_desfase(llm_data, real_data)

            total_offset += offset
            total_porcentaje += porcentaje
            n += 1
        except Exception as e:
            print(f"❌ Error en el caso {i+1}: {e}")

    if n > 0:
        print("\n📈 MÉTRICAS GLOBALES DE FASES:")
        print(f"   Offset medio global: {total_offset/n:.2f} segundos")
        print(f"   % de fases correctas global: {total_porcentaje/n:.2%}")
    else:
        print("⚠️ No se pudo procesar ningún caso de segmentación.")