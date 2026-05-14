from pymongo import MongoClient
from config.settings import MONGO_URL
from models.tasks import Task
import logging
from bson.objectid import ObjectId

logger = logging.getLogger(__name__)

class DBService:
    def __init__(self):
        self.client = MongoClient(MONGO_URL)
        self.db = self.client.task_scheduler
        self.task_collection = "tasks"

    def insert_tasks(self, tasks: list[Task]):
        try:
            task_dicts = [task.to_json() for task in tasks]
            self.db[self.task_collection].insert_many(task_dicts)
            logger.info(f"Inserted {len(tasks)} tasks into the database.")
        except Exception as e:
            logger.error(f"Error inserting tasks: {e}")

    def get_tasks(self,user_id:str) -> list[Task]:
        try:
            if user_id and ObjectId.is_valid(user_id):
                user_id=ObjectId(user_id)
            cursor = self.db[self.task_collection].find({"user_id": user_id})
            tasks = [Task.from_json(doc) for doc in cursor]
            return tasks
        except Exception as e:
            logger.error(f"Error fetching tasks: {e}")
            return []
    
    # def get_tasks(self,user_id:int) -> list[Task]:
    #     try:
    #         cursor = self.db[self.task_collection].aggregate([
    #             {
    #                 "$match":{
    #                     "user_id":user_id
    #                 }
    #             }
    #         ])

    #         tasks = [Task.from_json(doc) for doc in cursor]
    #         return tasks
    #     except Exception as e:
    #         logger.error(f"Error fetching tasks: {e}")
    #         return []
    
