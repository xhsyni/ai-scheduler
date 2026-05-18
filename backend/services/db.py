from pymongo import MongoClient
from config.settings import MONGO_URL, MONGO_DB
from models.tasks import Task
import logging
from bson.objectid import ObjectId
from models.conversation import Conversation, Message
from models.users import User

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
    def insert_tasks(self, tasks: list[Task]):
        try:
            task_dicts = [task.to_json() for task in tasks]
            self.db[self.task_collection].insert_many(task_dicts)
            logger.info(f"Inserted {len(tasks)} tasks into the database.")
        except Exception as e:
            logger.error(f"Error inserting tasks: {e}")

    def get_tasks_by_user_id(self,user_id:str) -> list[Task]:
        try:
            if user_id and ObjectId.is_valid(user_id):
                user_id=ObjectId(user_id)
            cursor = self.db[self.task_collection].find({"_id": user_id})
            tasks = [Task.from_json(doc) for doc in cursor]
            return tasks
        except Exception as e:
            logger.error(f"Error fetching tasks: {e}")
            return []

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
    
