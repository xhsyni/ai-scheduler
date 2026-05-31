docker tag scheduler:latest us-west1-docker.pkg.dev/automate-life-scheduler/backend/scheduler:latest
docker push us-west1-docker.pkg.dev/automate-life-scheduler/backend/scheduler:latest


uvicorn routers.main:app --host localhost --port 8000

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

Tools used by the agents:
1. get_current_datetime
2. get_user_tasks
3. check_schedule_conflict
4. create_schedule_task
5. add_task_into_schedule
6. update_task_in_schedule
8. get_user_memory
9. estimate_travel_time
10. recommend_collaboration_task
11. recommend_tasks_for_collaboration


General Sidebar Chatbot
-  communicate with voice 
|
add specific tasks from what time to what time, what location, reminder or not

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
