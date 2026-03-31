"""Ingest the BRIDGE Guide data into the knowledge base."""
import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from database import engine, async_session, init_db
from services.knowledge_service import knowledge_service


async def ingest():
    await init_db()

    # Load BRIDGE Guide data
    data_path = os.path.join(os.path.dirname(__file__), "..", "data", "bridge_guide.json")
    with open(data_path) as f:
        data = json.load(f)

    async with async_session() as db:
        # Ingest each resource
        print(f"Ingesting {len(data['resources'])} resources...")
        for i, resource in enumerate(data["resources"]):
            # Build rich content for each resource
            content_parts = [resource["description"]]

            if resource.get("eligibility"):
                content_parts.append(f"Eligibility: {resource['eligibility']}")
            if resource.get("cost"):
                content_parts.append(f"Cost: {resource['cost']}")
            if resource.get("contact_extra"):
                content_parts.append(f"Additional Contact: {resource['contact_extra']}")

            content = "\n\n".join(content_parts)

            await knowledge_service.ingest_document(
                db=db,
                title=resource["name"],
                category=resource["category"],
                content=content,
                url=resource.get("url"),
                phone=resource.get("phone"),
                source="bridge_guide",
                chunk_type="resource",
            )
            print(f"  [{i+1}/{len(data['resources'])}] {resource['name']}")

        # Ingest navigation guide as narrative chunks
        print("\nIngesting navigation guide...")
        for scenario, info in data["navigation_guide"].items():
            resources_list = ", ".join(info["resources"])
            content = (
                f"Navigation Scenario: {info['description']}\n"
                f"Priority: {info['priority']}\n"
                f"Recommended Resources: {resources_list}\n\n"
                f"If you are {info['description'].lower()}, these are the best resources to start with: {resources_list}."
            )
            await knowledge_service.ingest_document(
                db=db,
                title=f"Guide: {info['description']}",
                category="Navigation Guide",
                content=content,
                source="bridge_guide",
                chunk_type="narrative",
            )

        # Ingest key statistics
        print("Ingesting key statistics...")
        stats_content = (
            f"Source: {data['key_statistics']['source']}\n\n"
            + "\n".join(f"- {s}" for s in data["key_statistics"]["stats"])
        )
        await knowledge_service.ingest_document(
            db=db,
            title="Military Family Statistics (2025)",
            category="Statistics",
            content=stats_content,
            source="bridge_guide",
            chunk_type="narrative",
        )

        # Also try to load Road Home website data if available
        website_path = os.path.join(os.path.dirname(__file__), "..", "data", "roadhome_website.json")
        if os.path.exists(website_path):
            print("\nIngesting Road Home website content...")
            with open(website_path) as f:
                website_data = json.load(f)

            for page in website_data.get("pages", []):
                if page.get("content"):
                    await knowledge_service.ingest_document(
                        db=db,
                        title=page.get("title", "Road Home Page"),
                        category="Road Home Program",
                        content=page["content"],
                        url=page.get("url"),
                        source="website",
                        chunk_type="narrative",
                    )
                    print(f"  Ingested: {page.get('title', page.get('url', 'unknown'))}")

    total = knowledge_service.get_collection_count()
    print(f"\nIngestion complete! Total chunks in knowledge base: {total}")


if __name__ == "__main__":
    asyncio.run(ingest())
