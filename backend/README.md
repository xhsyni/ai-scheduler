
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


General Sidebar Chatbot
-  communicate with voice 
|
add specific tasks from what time to what time, what location, reminder or not


