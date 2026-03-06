from app.models.guide import Guide
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

    user_info = {
        "name": user.name,
        "height": user.height,
        "weight": user.weight,
        "allergies": user.allergies,
        "conditions": user.conditions,
    }

    guide_service = get_guide_service()
    content = await guide_service.generate(med_list, user_info)

    guide.content = content
    guide.status = "completed"
    await guide.save()
