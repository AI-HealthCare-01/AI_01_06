from app.models.guide import Guide
from app.models.patient_profile import PatientProfile
from app.models.prescription import Medication, Prescription
from app.models.user import User
from app.services.guide_service import get_guide_service


async def guide_task(ctx: dict, guide_id: int, user_id: int) -> None:
    """Generate a medication guide using LLM and save results."""
    guide = await Guide.get(id=guide_id)
    prescription = await Prescription.get(id=guide.prescription_id)
    user = await User.get(id=user_id)

    medications = await Medication.filter(prescription=prescription)
    med_list = [
        {
            "name": m.name,
            "dosage": m.dosage,
            "frequency": m.frequency,
            "duration": m.duration,
            "instructions": m.instructions,
        }
        for m in medications
    ]

    profile = await PatientProfile.get_or_none(user=user)
    user_info = {
        "birth_date": str(user.birth_date) if user.birth_date else None,
        "gender": user.gender,
        "has_profile": profile is not None,
        "height": float(profile.height_cm) if profile and profile.height_cm else None,
        "weight": float(profile.weight_kg) if profile and profile.weight_kg else None,
        "allergies": profile.allergy_details if profile else None,
        "conditions": profile.disease_details if profile else None,
    }

    guide_service = get_guide_service()
    try:
        content = await guide_service.generate(med_list, user_info)
        guide.content = content
        guide.status = "completed"
        prescription.ocr_status = "guide_completed"
    except BaseException:
        guide.status = "failed"
        raise
    finally:
        guide.profile_snapshot_at = profile.updated_at if profile else None
        await guide.save()
        await prescription.save()
