# Myelin Project Flowchart

This flowchart represents the high-level architecture of the Myelin AI Governance project, including the Frontend, Backend API, Orchestrator, Governance Pillars, and the Database (Supabase).

```mermaid
%%{init: {"theme": "neutral", "look": "handDrawn", "flowchart": {"curve": "basis"}, "themeVariables": {"mainBkg": "#ffffff", "primaryColor": "#ffffff", "clusterBkg": "#ffffff", "clusterBorder": "#000000"}}}%%
graph TD
    User((User))
    
    subgraph Client ["Frontend Client"]
        style Client fill:#fff,stroke:#333,stroke-width:2px,stroke-dasharray: 5 5
        UI["Demo UI / Dashboard (HTML/JS)"]
    end
    
    subgraph Backend ["Backend API"]
        style Backend fill:#fff,stroke:#333,stroke-width:2px,stroke-dasharray: 5 5
        API["FastAPI Server (api_server.py)"]
        Auth["Auth MiddleWare"]
    end
    
    subgraph Core ["Myelin Core System"]
        style Core fill:#fff,stroke:#333,stroke-width:2px,stroke-dasharray: 5 5
        Orch["Myelin Orchestrator"]
        
        subgraph Pillars ["Governance Pillars"]
            style Pillars fill:#fff,stroke:#333,stroke-width:2px,stroke-dasharray: 5 5
            Tox["Toxicity"]
            Gov["Governance"]
            Bias["Bias"]
            Fact["Factual (FCAM)"]
            Fair["Fairness"]
        end
    end
    
    subgraph Storage ["Supabase Database"]
        style Storage fill:#fff,stroke:#333,stroke-width:2px,stroke-dasharray: 5 5
        DB[("PostgreSQL\n(Users, Rules, Logs)")]
    end

    %% Data Flow
    User -- "1. Login / Request" --> UI
    UI -- "2. HTTP Request" --> API
    
    API -- "3. Validate Key" --> Auth
    Auth -.-> DB
    
    API -- "4. Analyze Content" --> Orch
    
    Orch -- "5. Fetch Custom Rules" --> DB
    DB -.-> Orch
    
    Orch -- "6. Parallel Evaluation" --> Tox
    Orch -- "6. Parallel Evaluation" --> Gov
    Orch -- "6. Parallel Evaluation" --> Bias
    Orch -- "6. Parallel Evaluation" --> Fact
    Orch -- "6. Parallel Evaluation" --> Fair
    
    Pillars -- "7. Rule Violations" --> Orch
    
    Orch -- "8. Aggregated Result" --> API
    API -- "9. Audit Log" --> DB
    API -- "10. JSON Response" --> UI
    UI -- "11. Display Result" --> User
```

## How to View
This diagram uses the `look: handDrawn` feature of Mermaid.js. 
- **GitHub**: Renders natively in the file viewer.
- **VS Code**: Install "Markdown Preview Mermaid Support" or "Mermaid Editor" to view.
