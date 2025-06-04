import csv
import json
from datetime import datetime
from uuid import uuid4

def load_transcription(file_path):
    with open(file_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return [
            {
                "start": float(row["start"]),
                "end": float(row["end"]),
                "speaker": row["speaker"].lower(),
                "transcription": row["transcription"]
            } for row in reader
        ]

def load_json(file_path):
    with open(file_path, encoding='utf-8') as f:
        return json.load(f)


def build_clinical_segments(fases):
    labels = {
        "🟢": "courtesy",
        "🟠": "symptoms",
        "🔵": "diagnosis",
        "🔴": "treatment",
        "⚪": "closure"
    }
    segments = {}
    for f in fases:
        key = labels.get(f["icono"], "other")
        segments[key] = {
            "time_range": f["tiempo"],
            "description": f["resumen"]
        }
    return segments

def extract_symptoms(hechos):
    return hechos.get("Paciente", [])


def build_transcription_structure(transcription_data):
    return {
        "segments": transcription_data
    }
    
# Crear JSON final
def build_final_json(path):    
    transcription_data = load_transcription(path+"_cleaned_text_and_roles.csv")
    resumen_fases = load_json(path+"_clinic_segmentation.json")
    anotaciones = load_json(path+"_medical_concepts.json")
    hechos = load_json(path+"_symptoms.json")
    diagnosis = load_json(path+"_diagnosis.json")
    role_map = {
        "paciente": "patient",
        "medico": "doctor",
        "especialista": "specialist"
    }

    speakers_present = sorted(set(
        role_map.get(entry["speaker"].lower(), entry["speaker"]) for entry in transcription_data
    ))
    final_json = {
        "session_id": str(uuid4()),
        "timestamp": datetime.now().isoformat(),
        "speakers": speakers_present,
        "clinical_segments": build_clinical_segments(resumen_fases["resumen_fases"]),
        "medical_concepts": {
            "specialist": anotaciones.get("especialista", {}),
            "doctor": anotaciones.get("medico", {}),
            "patient": anotaciones.get("paciente", {})
        },
        "extracted_symptoms": extract_symptoms(hechos),
        "dss_diagnosis": diagnosis,
        "conversation": build_transcription_structure(transcription_data)
    }
    with open(path + "_clinic_session.json", "w", encoding="utf-8") as out_file:
        json.dump(final_json, out_file, ensure_ascii=False, indent=2)
    return final_json