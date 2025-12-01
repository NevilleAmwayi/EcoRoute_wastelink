# 🌿 WasteLink — Transforming Urban Waste Into Circular Value  
# A Multi-Stakeholder Smart Waste Management Ecosystem

WasteLink is an AI-powered, community-driven, circular-economy platform built to solve urban waste challenges in African cities.  
We connect *households, waste collectors, recycling companies, local governments, and marketplaces* into one efficient ecosystem — using *LLMs, JAC agents, IoT-ready extensions, and transparent data flows.*

## 🚀 Problem We Are Solving  
Urban areas face a critical waste crisis:

- Inefficient collection systems  
- Plastic, organic & electronic waste piling up  
- Lack of incentives for households  
- Limited recycling transparency  
- Fragmented stakeholders  
- Rising methane emissions from poorly managed dumpsites  

Communities want cleaner cities.  
Collectors want structured routes.  
Recyclers want reliable supply.  
Governments want data.  
African cities need scalable systems.

## 🌍 Our Impact Goals (Aligned With SDGs)

WasteLink directly contributes to **six major SDGs**:
### SDG 8— Decent Work & Economic Growth
- creates new job opportunities
- formalizes the informal waste sector
- stimulates green economic participation

### SDG 10— Reduced Inequalities
- Includes low-income households
- Elevate marginalized workers
- Multi-stakeholder fairness
  
### **SDG 11 — Sustainable Cities & Communities**  
- Reduces urban pollution  
- Creates structured waste collection routes  
- Enhances sanitation + public health  
- Improves city data systems  

### **SDG 12 — Responsible Consumption & Production**  
- Encourages responsible household waste sorting  
- Incentivizes recycling through rewards  
- Builds circular-economy habits  

### **SDG 13 — Climate Action**  
- Organic waste → compost → reduced methane  
- Less landfill burning = lower CO₂  
- Promotes climate-positive behaviors  

### **SDG 17 — Partnerships for the Goals**  
- Multi-stakeholder model connecting:  
  ✔ communities  
  ✔ collectors  
  ✔ recyclers  
  ✔ county governments  
  ✔ climate-impact partners  
  ✔ SMEs / green businesses  

# 🧩 Core Features

### 🟩 **1. Household Waste Sorting Interface**  
- Users log plastic, paper, glass, organic waste  
- Gamified points system  
- “Waste diary” for personal tracking  
- LLM-powered assistant teaches sorting  

### 🟦 **2. Smart Collector Module**  
- AI-optimized routes using JAC walkers  
- Collector performance tracking  
- Real-time waste pickup logs  

### 🟪 **3. Recycler & Aggregator Dashboard**  
- Predictable feedstock supply  
- Material sorting data  
- Market-price insights  

### 🟧 **4. Marketplace for Recycled Items**  (future)
- SMEs can buy recycled material  
- Eco-friendly brands can list products  

### 🟨 **5. Local Government Dashboard**  (future)
- Waste heatmaps  
- Environmental impact metrics  
- Emissions reduction data  
- Reports for planning  


# 🧠 Tech Stack

### **Language:**  
Jac Language
Used for:
✔ Modeling users (Resident, Collector, Admin)
✔ Creating Collection nodes
✔ Automating assignment using walkers
✔ Managing relationships between nodes

Python (FastAPI / Flask)
Used for:
✔ Waste classification using AI
✔ Simple routing logic
✔ API endpoints linking frontend ↔ backend

Frontend
✔ React Native / Jac-Client
✔ Simple mobile UI for Resident & Collector
✔ Web admin dashboard

Database
✔ SQLite / PostgreSQL (simple for hackathon)

### **Architecture:**  
- Multi-agent system using **JAC walkers, nodes & edges**  
- Agentic orchestration  
- LLM-powered classification  
- Modular, scalable design  

### PROJECT STRUCTURE 
WasteLink/
│
├── backend/
│   ├── jac/
│   │   ├── resident.jac
│   │   ├── collector.jac
│   │   ├── admin.jac
│   │   ├── collection.jac
│   │   └── flows.jac
│   │
│   └── python/
│       ├── ai_model.py
│       ├── api.py
│       └── utils.py
│
├── frontend/
│   ├── resident-app/
│   ├── collector-app/
│   └── admin-dashboard/
│
└── README.md

## **Jac Skeleton (MVP Logic)**

node Resident:
    has name: str
    has phone: str
    has location: str
    can request_pickup

    ability request_pickup(waste_type: str, photo: str):
        spawn Collection(waste_type=waste_type, status="requested")


node Collector:
    has name: str
    has is_available: bool
    can accept_job, complete_job

    ability accept_job(collection: Collection):
        collection.status = "collector_assigned"
        collection.assigned_to = self

    ability complete_job(collection: Collection):
        collection.status = "completed"


node Admin:
    can assign_collector

    walker assign_collector:
        for c: Collector where c.is_available:
            for r: Resident.<Collection>:
                if r.status == "requested":
                    c.accept_job(r)
                    break


node Collection:
    has waste_type: str
    has status: str
    has assigned_to: Collector

### **🔌 API Endpoints (Python)**

POST /classify

Classifies waste type from image using AI.

POST /pickup

Resident requests a pickup.

GET /collector/jobs

Collector sees assigned tasks.

PUT /collector/complete

Collector marks job as done.

GET /admin/stats

Admin dashboard analytics.

### **Testing Instructions**

1. Clone repository
git clone <repo-url>

2. Install dependencies
pip install -r requirements.txt

3. Run Python server
uvicorn api:app --reload

4. Run Jac flows
jac run flows.jac

5. Run frontend
npm install  
npm start

🧑‍🤝‍🧑 Team Roles

### **Hawi Emanuela — Project Manager & Systems Strategist**
- Architecture  
- SDG alignment  
- Proposal development  
- Workflow coordination  

### **Neville Shem — Full-Stack JAC Developer**
- Walker design  
- Backend logic  
- Integrations  

### **Eric Nzioka — UI/UX + Frontend Builder**
- User interface  
- Icons + visual flow  
- User onboarding screens

 
# All team members are JAC engineers, bringing strong coding skills and collaborative problem-solving to the project.


# 🔗 License  
MIT License.



# 🌱 Final Note  
WasteLink isn’t just a project —  
it is a **scalable climate-tech ecosystem** co-created by young African innovators to transform cities into clean, circular communities.


