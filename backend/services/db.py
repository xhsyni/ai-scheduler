import certifi
import pymongo
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from config.settings import MONGO_URL, MONGO_DB
from models.tasks import Task
import logging
from bson.objectid import ObjectId
from models.conversations import Conversation, Message
from models.users import User
from models.tasks import GroupTask
from utils.timezone import now_myt,to_myt, to_utc
from datetime import datetime,timedelta

logger = logging.getLogger(__name__)

class DBService:
    def __init__(self):
        self.client = MongoClient(MONGO_URL)
        try:
            self.client.admin.command('ping')
            logger.info("✅ MongoDB connected successfully")
        except Exception as e:
            logger.error("❌ MongoDB connection failed: %s", e)
        self.db = self.client[MONGO_DB]
        self.user_collection = "users"
        self.task_collection = "tasks"
        self.conversation_collection = "conversations"
        self.message_collection = "messages"
    
    # Users Database Functions
    def get_user_by_email(self,email:str) -> User:
        try:
            cursor = self.db[self.user_collection].find_one({"email": email})
            if not cursor:
                return None
            user = User.from_json(cursor)
            return user
        except Exception as e:
            logger.error(f"Error fetching user: {e}")
            return None

    def insert_user(self,user:User):
        try:
            user_dict = user.to_json()
            self.db[self.user_collection].insert_one(user_dict)
            logger.info(f"Inserted user into the database.")
        except Exception as e:
            logger.error(f"Error inserting user: {e}")

    def get_user_by_id(self, user_id: str) -> User:
        try:
            cursor = self.db[self.user_collection].find_one({"_id": ObjectId(user_id)})
            if not cursor:
                return None
            return User.from_json(cursor)
        except Exception as e:
            logger.error(f"Error fetching user: {e}")
            return None 

    def get_all_users(self) -> list[User]:
        try:
            cursor = self.db[self.user_collection].find()
            return [User.from_json(doc) for doc in cursor]
        except Exception as e:
            logger.error(f"Error fetching all users: {e}")
            return []
    
    # Tasks Database Functions
    def get_tasks_by_user_id_and_date(self, user_id: str, start_time, end_time=None) -> list[Task]:
        try:
            if isinstance(start_time, str):
                start_time = datetime.strptime(start_time, "%Y-%m-%d")
            if end_time is None:
                end_time = start_time + timedelta(days=1)
            elif isinstance(end_time, str):
                end_time = datetime.strptime(end_time, "%Y-%m-%d")

            cursor = self.db[self.task_collection].find({
                "users.user_id": user_id,
                "start_time": {
                    "$gte": start_time,
                    "$lt": end_time
                }
            })
            return [Task.from_json(doc) for doc in cursor]
        except Exception as e:
            logger.error(f"Error fetching tasks: {e}")
            return []

    def get_tasks_by_user_id_and_title(self,keyword,query_embedding,user_id,start_time,end_time=None,limit=10):
        numCandidate = min(limit * 6, 1000)
        if isinstance(start_time, str):
            start_date = to_utc(datetime.strptime(start_time, "%Y-%m-%d"))
        else:
            start_date = to_utc(start_time)
            
        if end_time is None:
            end_date = to_utc(start_date + timedelta(days=1))
        elif isinstance(end_time, str):
            end_date = to_utc(datetime.strptime(end_time, "%Y-%m-%d"))
        else:
            end_date = to_utc(end_time)
            
        try:
            if query_embedding and len(query_embedding) > 0:
                vector_pipeline = [
                    {
                        "$vectorSearch": {
                            "queryVector": query_embedding,
                            "path": "embeddings",
                            "numCandidates": numCandidate, 
                            "limit": limit, 
                            "index": "vector_index"
                        }
                    },
                    {
                        "$match": {
                            "users.user_id": user_id,
                            "start_time": {
                                "$gte": start_date,
                                "$lt": end_date
                            }
                        }
                    },
                    {"$addFields": {"score": {"$meta": "vectorSearchScore"}}}
                ]
                vector_results = list(self.db[self.task_collection].aggregate(vector_pipeline))
            if keyword:
                if isinstance(keyword, str):
                    keyword = [keyword]

                keyword_pipeline = [
                    {
                        "$search": {
                            "text": {
                                "query": keyword,
                                "path": [
                                    "title",
                                    "description"
                                ]
                            }
                        }
                    },
                    {"$addFields": {"score": {"$meta": "searchScore"}}},
                    {"$match": {"users.user_id": user_id}}
                ]
                keyword_results = list(self.db[self.task_collection].aggregate(keyword_pipeline))
            return vector_results,keyword_results
        except Exception as e:
            logger.error(f"Error fetching tasks: {e}")
            return []

    def get_task_by_id(self, task_id: str) -> Task:
        try:
            cursor = self.db[self.task_collection].find_one({"_id": ObjectId(task_id)})
            if not cursor:
                return None
            return Task.from_json(cursor)
        except Exception as e:
            logger.error(f"Error fetching task: {e}")
            return None 

    def insert_tasks(self, tasks: list[Task]) -> list[str]:
        try:
            task_dicts = [task.to_json() for task in tasks]
            result = self.db[self.task_collection].insert_many(task_dicts)
            logger.info(f"Inserted {len(tasks)} tasks into the database.")
            return [str(inserted_id) for inserted_id in result.inserted_ids]
        except Exception as e:
            logger.error(f"Error inserting tasks: {e}")
            return []

    def user_exists_in_task(self, task_id: str, user_id: str) -> bool:
        try:
            task = self.db[self.task_collection].find_one({
                "_id": ObjectId(task_id),
                "users.user_id": user_id
            })

            return task is not None

        except Exception as e:
            logger.error(f"Error checking user in task: {e}")
            return False

    def update_task(self, task_id: str, updated_task: Task):
        """Replace updatable fields on a task using $set. None values are ignored."""
        try:
            data = updated_task.to_json()
            # Remove fields that should never be overwritten on update
            data.pop("task_id", None)
            data.pop("created_at", None)
            data.pop("users", None)  # manage users separately
            # Only keep fields that were actually provided (not None)
            data = {k: v for k, v in data.items() if v is not None}
            if not data:
                logger.warning(f"No fields to update for task {task_id}")
                return
            self.db[self.task_collection].update_one(
                {"_id": ObjectId(task_id)},
                {"$set": data}
            )
            logger.info(f"Updated task {task_id} with fields: {list(data.keys())}")
        except Exception as e:
            logger.error(f"Error updating task: {e}")

    def add_user_to_task(self, task_id: str, group_task: GroupTask):
        """Append a new user entry to the task's users array ($push)."""
        try:
            self.db[self.task_collection].update_one(
                {"_id": ObjectId(task_id)},
                {"$push": {"users": group_task.to_json()}}
            )
            logger.info(f"Added user to task {task_id}")
        except Exception as e:
            logger.error(f"Error adding user to task: {e}")

    def update_user_role_in_task(self, task_id: str, user_id: str, new_role: str):
        """Update the role of a specific user inside the task's users array."""
        try:
            result = self.db[self.task_collection].update_one(
                {"_id": ObjectId(task_id), "users.user_id": user_id},
                {"$set": {"users.$.role": new_role}}
            )
            if result.matched_count == 0:
                logger.warning(f"No matching user {user_id} found in task {task_id}")
                return False
            logger.info(f"Updated role of user {user_id} in task {task_id} to {new_role}")
            return True
        except Exception as e:
            logger.error(f"Error updating user role in task: {e}")
            return False

    def delete_user_from_task(self, task_id: str, user_id: str):
        """Remove a user from the task's users array."""
        try:
            result = self.db[self.task_collection].update_one(
                {"_id": ObjectId(task_id)},
                {"$pull": {"users": {"user_id": user_id}}}
            )

            if result.matched_count == 0:
                logger.warning(f"No matching task {task_id} found")
                return False

            if result.modified_count == 0:
                logger.warning(f"User {user_id} not found in task {task_id}")
                return False

            logger.info(f"Deleted user {user_id} from task {task_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting user from task: {e}")
            return False

    def delete_task(self, task_id: str) -> bool:
        try:
            result = self.db[self.task_collection].delete_one({"_id": ObjectId(task_id)})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting task: {e}")
            return False

    # Conversation Database Functions
    def insert_conversation(self, conversation: Conversation):
        try:
            conversation_dict = conversation.to_json()
            result = self.db[self.conversation_collection].insert_one(conversation_dict)
            logger.info(f"Inserted conversation into the database.")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error inserting conversation: {e}")
            return None

    def get_conversations_by_user_id(self, user_id: str) -> list[Conversation]:
        try:
            cursor = self.db[self.conversation_collection].find({"user_id": user_id}).sort("created_at", -1)
            conversations = [Conversation.from_json(doc) for doc in cursor]
            return conversations
        except Exception as e:
            logger.error(f"Error fetching conversations: {e}")
            return []

    def get_conversation_by_user_id_and_task_id(self, user_id: str, task_id: str) -> Conversation:
        try:
            cursor = self.db[self.conversation_collection].find_one({"user_id": user_id, "task_id": task_id})
            return Conversation.from_json(cursor) if cursor else None
        except Exception as e:
            logger.error(f"Error fetching conversation: {e}")
            return None

    def get_conversation(self, conversation_id: str) -> Conversation:
        try:
            query = {"_id": ObjectId(conversation_id)} if ObjectId.is_valid(conversation_id) else {"conversation_id": conversation_id}
            cursor = self.db[self.conversation_collection].find_one(query)
            return Conversation.from_json(cursor) if cursor else None
        except Exception as e:
            logger.error(f"Error fetching conversation: {e}")
            return None

    # Message Database Functions
    def insert_message(self, message: Message):
        try:
            message_dict = message.to_json()
            result = self.db[self.message_collection].insert_one(message_dict)
            logger.info(f"Inserted message into the database.")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error inserting message: {e}")
            return None

    def get_messages(self, conversation_id: str) -> list[Message]:
        try:
            cursor = self.db[self.message_collection].find({"conversation_id": conversation_id}).sort("created_at", 1)
            messages = [Message.from_json(doc) for doc in cursor]
            return messages
        except Exception as e:
            logger.error(f"Error fetching messages: {e}")
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

    # Reminder Database Functions
    def get_upcoming_reminder_tasks(self, now: datetime, window_end: datetime) -> list[dict]:
        """
        Find tasks where reminder=True, reminder_sent is not True,
        and start_time falls within [now, window_end].
        Returns raw dicts (not Task objects) so we can access user info easily.
        """
        try:
            cursor = self.db[self.task_collection].find({
                "reminder": True,
                "reminder_sent": {"$ne": True},
                "start_time": {
                    "$gte": now,
                    "$lte": window_end
                }
            })
            return list(cursor)
        except Exception as e:
            logger.error(f"Error fetching upcoming reminder tasks: {e}")
            return []

    def mark_reminder_sent(self, task_id: str):
        """Set reminder_sent=True on a task document to prevent duplicate emails."""
        try:
            self.db[self.task_collection].update_one(
                {"_id": ObjectId(task_id)},
                {"$set": {"reminder_sent": True}}
            )
            logger.info(f"Marked reminder_sent=True for task {task_id}")
        except Exception as e:
            logger.error(f"Error marking reminder sent for task {task_id}: {e}")

