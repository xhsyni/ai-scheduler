
uvicorn routers.app:app --host localhost --port 8000

# Orchestrator Agent (ai_scheduler_orchestrator_main )
Main Agent for the AI Scheduler that is responsible for receiving the user request and routing them to other sub-agents. It can trigger multiple agents to complete the user's request.
1. Activity Planner Agent 
    - Goal 
    - Priority estimation
    - Time estimation
    - Schedule optimization
    - Task Generation
2. Calendar Scheduler Agent 
    - Check timeslot 
    - Detect conflicts
    - Free slot suggestion (optimization)
3. Memory Agent (Social)
    - Store long-term habits
    - Store preferences
    - Track productivity
    - Track group behavior
    - Conversation memory
4. Travel Agent 
    - Traffic analysis
    - Route optimization
    - Travel duration
    - Departure recommendations
    - Meetup midpoint calculations
5. Recommendation Agent 
    - Search activities
    - Rank options
    - Personalization
    - Group preference balancing
    - Cost optimization
    - Suggests activities arrangement based on the activity

## Tools
1. Database Service - to access the database for storing and retrieving information.
2. Google Calendar Service - to access the user's Google Calendar for scheduling and retrieving events.
3. Google Maps - to get the distance and travel time between two locations.
4. Google Search Engine - to search for relevant information based on the user's request. 

If the recommendation is accepted by the users, then it will be saved in the database. If rejected, it will not be saved in the database.

['get_user_tasks', 'check_schedule_conflict', 'create_schedule_task', 'add_task_into_schedule', 'get_user_memory', 'estimate_travel_time', 'recommend_collaboration_task', 'recommend_tasks_for_collaboration']

General Sidebar Chatbot
-  communicate with voice 
|
add specific tasks from what time to what time, what location, reminder or not


{'users': [{'user_id': '6a0bf7fe0d1d187a4fe5cf61', 'name': 'xuan han', 'role': 'owner', 'updated_by': None, 'updated_at': '2026-05-20T21:05:04.292966+08:00'}], 'title': 'Meeting with Han', 'description': 'Meeting with Han', 'priority': 'mid', 'location': None, 'start_time': '2026-05-20T22:00:00+08:00', 'end_time': '2026-05-20T23:00:00+08:00', 'duration': 60, 'reminder': True, 'status': 'scheduled', 'created_at': '2026-05-20T21:05:04.293000+08:00', 'updated_at': '2026-05-20T21:05:04.292974+08:00'}


flowchart LR
  User["User message"] --> RecAgent["recommendation_agent"]
  RecAgent --> Tool["recommend_tasks_for_collaboration"]
  Tool --> Rec["_recommend_collaboration_task"]
  Rec --> Title["title = objective OR default"]
  Rec --> Reason["reasoning = hardcoded string"]
  Tool --> Sched["_add_task_into_schedule"]
  User --> Dest["destination → location ✓"]
  Dest --> Sched
  Title --> Sched
  Reason --> Sched["description = reasoning ✗"]
