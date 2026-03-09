from app.models.audit import AuditLog


async def log_action(
    actor_id: int,
    action_type: str,
    ip_address: str,
    resource_type: str | None = None,
    resource_id: str | None = None,
    outcome: str = "SUCCESS",
) -> None:
    await AuditLog.create(
        actor_id=actor_id,
        action_type=action_type,
        ip_address=ip_address,
        resource_type=resource_type,
        resource_id=resource_id,
        outcome=outcome,
    )
