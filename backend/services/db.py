from pymongo import MongoClient
from config.settings import MONGO_URL, MONGO_DB
from models.tasks import Task
import logging
from bson.objectid import ObjectId
from models.conversations import Conversation, Message
from models.users import User
from models.tasks import GroupTask

logger = logging.getLogger(__name__)

class DBService:
    def __init__(self):
        self.client = MongoClient(MONGO_URL)
        try:
            self.client.admin.command('ping')
            logger.info("✅ MongoDB connected successfully")
        except Exception as e:
            logger.error(f"❌ MongoDB connection failed: {e}")
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

    # Tasks Database Functions
    def get_task_by_id(self, task_id: str) -> Task:
        try:
            cursor = self.db[self.task_collection].find_one({"_id": ObjectId(task_id)})
            if not cursor:
                return None
            return Task.from_json(cursor)
        except Exception as e:
            logger.error(f"Error fetching task: {e}")
            return None 

    def insert_tasks(self, tasks: list[Task]):
        try:
            task_dicts = [task.to_json() for task in tasks]
            self.db[self.task_collection].insert_many(task_dicts)
            logger.info(f"Inserted {len(tasks)} tasks into the database.")
        except Exception as e:
            logger.error(f"Error inserting tasks: {e}")

    def get_tasks_by_user_id(self,user_id:str) -> list[Task]:
        try:
            cursor = self.db[self.task_collection].find({"users.user_id": {"$eq": user_id}})
            tasks = [Task.from_json(doc) for doc in cursor]
            return tasks
        except Exception as e:
            logger.error(f"Error fetching tasks: {e}")
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

    # Conversation Database Functions
    def insert_conversation(self, conversation: Conversation):
        try:
            conversation_dict = conversation.to_json()
            self.db[self.conversation_collection].insert_one(conversation_dict)
            logger.info(f"Inserted conversation into the database.")
        except Exception as e:
            logger.error(f"Error inserting conversation: {e}")

    # Message Database Functions
    def insert_message(self, message: Message):
        try:
            message_dict = message.to_json()
            self.db[self.message_collection].insert_one(message_dict)
            logger.info(f"Inserted message into the database.")
        except Exception as e:
            logger.error(f"Error inserting message: {e}")

    def get_conversation_by_user_id_and_task_id(self,user_id:str,task_id:str) -> Conversation:
        try:
            if user_id and ObjectId.is_valid(user_id):
                user_id=ObjectId(user_id)
            if task_id and ObjectId.is_valid(task_id):
                task_id=ObjectId(task_id)
            cursor = self.db[self.conversation_collection].find_one({"_id": user_id, "task_id": task_id})
            conversation = Conversation.from_json(cursor)
            return conversation
        except Exception as e:
            logger.error(f"Error fetching conversation: {e}")
            return None

    def get_message(self,conversation_id:str) -> list[Message]:
        try:
            if conversation_id and ObjectId.is_valid(conversation_id):
                conversation_id=ObjectId(conversation_id)
            cursor = self.db[self.message_collection].find({"conversation_id": conversation_id})
            messages = [Message.from_json(doc) for doc in cursor]
            return messages
        except Exception as e:
            logger.error(f"Error fetching messages: {e}")
            return []
    
    def get_conversation(self,conversation_id:str) -> Conversation:
        try:
            if conversation_id and ObjectId.is_valid(conversation_id):
                conversation_id=ObjectId(conversation_id)
            cursor = self.db[self.conversation_collection].find_one({"conversation_id": conversation_id})
            conversation = Conversation.from_json(cursor)
            return conversation
        except Exception as e:
            logger.error(f"Error fetching conversation: {e}")
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
    
