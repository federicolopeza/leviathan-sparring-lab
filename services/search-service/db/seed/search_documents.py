from __future__ import annotations

import asyncio

from sqlalchemy import func, select

from app.database import SessionLocal
from app.models import IndexedDocument

ORG_A = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
ORG_B = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"


def _documents() -> list[IndexedDocument]:
    topics = [
        "Pagos instantaneos",
        "Creditos pyme",
        "Open finance",
        "Billetera digital",
        "KYC remoto",
        "Riesgo transaccional",
        "Remesas regionales",
        "Factoring digital",
        "Tarjetas prepagas",
        "Scoring alternativo",
    ]
    countries = ["Uruguay", "Argentina", "Brasil", "Chile", "Colombia"]
    documents: list[IndexedDocument] = []
    for index in range(50):
        country = countries[index % len(countries)]
        topic = topics[index % len(topics)]
        org_id = ORG_A if index < 30 else ORG_B
        documents.append(
            IndexedDocument(
                org_id=org_id,
                title=f"{country} fintech brief {index + 1}: {topic}",
                body=(
                    f"Reporte ficticio LATAM sobre {topic.lower()} en {country}. "
                    "Incluye adopcion bancaria, comercios, conciliacion y controles AML."
                ),
                tags=["latam", country.lower(), topic.lower().replace(" ", "-")],
            )
        )
    return documents


async def seed() -> None:
    async with SessionLocal() as session:
        existing = await session.scalar(select(func.count(IndexedDocument.id)))
        if existing:
            return
        session.add_all(_documents())
        await session.commit()


if __name__ == "__main__":
    asyncio.run(seed())
