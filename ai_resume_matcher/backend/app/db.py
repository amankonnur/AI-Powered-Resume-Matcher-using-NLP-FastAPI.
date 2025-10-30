# app/db.py
import motor.motor_asyncio
from bson.objectid import ObjectId
import os

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
db = client["resume_matcher"]

async def save_resume_doc(doc):
    res = await db.resumes.insert_one(doc)
    return str(res.inserted_id)

async def get_resume_by_id(rid):
    return await db.resumes.find_one({"_id": ObjectId(rid)})
