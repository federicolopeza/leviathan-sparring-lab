from __future__ import annotations

from dataclasses import dataclass

from app.models import NotificationTemplate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass(frozen=True)
class TemplateSeed:
    code: str
    subject_template: str
    body_template: str
    locale: str = "es"


DEFAULT_TEMPLATES: tuple[TemplateSeed, ...] = (
    TemplateSeed(
        code="welcome",
        subject_template="Bienvenido a Melispy, {{ first_name|default('equipo') }}",
        body_template=(
            "Tu cuenta ya está activa. Desde ahora podés revisar pagos, alertas y actividad "
            "operativa desde tu panel Melispy."
        ),
    ),
    TemplateSeed(
        code="invoice_issued",
        subject_template="Factura {{ invoice_number }} emitida",
        body_template=(
            "Emitimos la factura {{ invoice_number }} por {{ amount|default('tu plan') }}. "
            "La dejamos disponible para tu administración."
        ),
    ),
    TemplateSeed(
        code="password_reset",
        subject_template="Restablecé tu contraseña de Melispy",
        body_template=(
            "Recibimos una solicitud para cambiar tu contraseña. Usá este enlace: "
            "{{ reset_url }}. Si no fuiste vos, ignorá este mensaje."
        ),
    ),
    TemplateSeed(
        code="magic_link",
        subject_template="Tu acceso seguro a Melispy",
        body_template=(
            "Entrá con este enlace de acceso único: {{ magic_url }}. Expira pronto por seguridad."
        ),
    ),
    TemplateSeed(
        code="member_invitation",
        subject_template="{{ inviter|default('Tu equipo') }} te invitó a Melispy",
        body_template=(
            "Tenés una invitación para sumarte a {{ org_name|default('tu organización') }}. "
            "Aceptala desde {{ invitation_url }}."
        ),
    ),
)


async def seed_notification_templates(db: AsyncSession) -> None:
    existing = await db.execute(select(NotificationTemplate.code))
    existing_codes = set(existing.scalars().all())
    for template in DEFAULT_TEMPLATES:
        if template.code in existing_codes:
            continue
        db.add(
            NotificationTemplate(
                code=template.code,
                subject_template=template.subject_template,
                body_template=template.body_template,
                locale=template.locale,
            )
        )
