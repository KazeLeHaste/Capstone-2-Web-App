# CHAPTER 2 APPENDIX: MARKET FEASIBILITY STUDY AND CONTEXT DIAGRAM

## Traffic Simulator: Analysis and Recommendation of Effect in Traffic Management Strategies

**Capstone Project**  
**University of Perpetual Help System-DALTA-Molino Campus**  
**Bachelor of Science in Information Technology**

---

# SECTION 1: MARKET FEASIBILITY STUDY

## 1.1 Introduction

This Market Feasibility Study evaluates the viability of the **Traffic Simulator: Analysis and Recommendation of Effect in Traffic Management Strategies** as a decision-support tool for traffic management in the Philippine context. The study examines target markets, existing competition, and the demand for such systems to determine the project's potential for adoption and sustainability.

---

## 1. 2 Target Market(s) / User Segments

The Traffic Simulator addresses the needs of multiple stakeholder groups within the traffic management and urban planning ecosystem.  Based on the system's design and functionality, the following user segments have been identified:

### 1.2.1 Primary Target Markets

| **User Segment** | **Description** | **Primary Needs** | **System Value Proposition** |
|------------------|-----------------|-------------------|------------------------------|
| **Local Government Units (LGUs)** | City and municipal traffic management departments such as Bacoor Traffic Management Department (BTMD) | Data-driven decision support for traffic interventions; evidence-based budget justifications | Enables simulation-based testing of traffic strategies before real-world implementation; generates quantitative reports for policy proposals |
| **Traffic Management Authorities** | Regional and national traffic enforcement agencies (e.g., MMDA, provincial traffic offices) | Tools to evaluate signal timing, road configurations, and enforcement strategies | Provides comparative analytics across multiple scenarios; supports adaptive signal control evaluation |
| **Urban Planners** | City planning departments and consultants responsible for infrastructure development | Predictive modeling for infrastructure investments; congestion impact assessment | Offers visualization of traffic flow under various configurations; calculates KPIs such as throughput, delay, and emissions |

### 1.2.2 Secondary Target Markets

| **User Segment** | **Description** | **Primary Needs** | **System Value Proposition** |
|------------------|-----------------|-------------------|------------------------------|
| **Educational Institutions** | Universities offering Transportation Engineering, Urban Planning, and IT programs | Teaching tools for traffic simulation and system development | Provides accessible interface to professional-grade SUMO simulation; serves as capstone/thesis platform |
| **Policy Makers and Transport Researchers** | Government agencies (DOTr, NEDA) and research institutions | Empirical data for policy formulation; scenario-based impact studies | Generates localized simulation evidence; supports Build Better More and smart city initiatives |
| **Private Sector Developers** | Real estate developers, mall operators, commercial establishments | Traffic impact assessments for new developments | Enables simulation of traffic effects from proposed projects; supports EIA and permit applications |

### 1.2.3 Market Size Estimation (Philippine Context)

| **Segment** | **Estimated Number** | **Potential Users per Entity** |
|-------------|----------------------|-------------------------------|
| Cities and Municipalities in Metro Manila and CALABARZON | 33+ LGUs | 5-15 traffic personnel per LGU |
| Provincial Traffic Offices (Cavite, Laguna, Batangas, Rizal, Quezon) | 5 provinces | 10-20 planners and enforcers |
| Universities with Engineering/IT Programs | 50+ institutions | 100-500 students annually |
| Private Developers (Major Projects) | 100+ active projects annually | 2-5 planners per project |

**Total Addressable Market (TAM) Estimate:**
- **LGU Segment:** 165–495 potential users across CALABARZON
- **Academic Segment:** 5,000–25,000 students annually (nationwide)
- **Private Sector:** 200–500 planners annually

---

## 1.3 Existing Competition

The traffic simulation software market is experiencing significant growth globally, with estimates ranging from **$1.5 billion to $2.5 billion in 2024**, projected to reach **$2.7 billion to $3.2 billion by 2025**, maintaining a compound annual growth rate (CAGR) of **6.9%–13.2%** through the decade (Verified Market Reports, 2024; Growth Market Reports, 2024).

### 1.3.1 Global Competitors

| **Software** | **Developer** | **Type** | **Licensing** | **Strengths** | **Weaknesses** |
|--------------|---------------|----------|---------------|---------------|----------------|
| **PTV Vissim/Visum** | PTV Group (Germany) | Microscopic/Macroscopic | Commercial (₱500,000–₱2,000,000+/license) | High precision; global presence; extensive validation; professional support | Expensive; requires specialized training; not localized for Philippine conditions |
| **Aimsun Next** | Aimsun (Spain) | Hybrid (Micro/Meso/Macro) | Commercial (₱400,000–₱1,500,000+/license) | AI-driven optimization; real-time controls; multi-modal simulation | High cost; complex interface; limited Philippine deployment |
| **SUMO** | DLR (Germany) | Microscopic | Open Source (Free) | Free; highly customizable; active community; TraCI API for integration | Steep learning curve; limited GUI; requires technical expertise; no professional support |
| **Synchro/SimTraffic** | Trafficware/Bentley Systems | Microscopic | Commercial (₱200,000–₱500,000/license) | Signal optimization focus; industry standard in US | Limited scenario complexity; not optimized for Philippine traffic patterns |
| **Paramics** | Quadstone | Microscopic | Commercial | Fast simulation; good visualization | Declining market presence; limited updates |

### 1. 3.2 Local/Regional Context

| **Solution** | **Description** | **Limitations** |
|--------------|-----------------|-----------------|
| **MMDA Traffic Engineering Center** | In-house tools for Metro Manila traffic management | Not publicly available; limited to MMDA operations |
| **Academic Projects (Various Universities)** | Thesis-level traffic simulations | Typically single-intersection focus; lack comprehensive analytics and user interface |
| **Manual Traffic Studies** | Traditional observation-based assessments | Time-consuming; limited predictive capability; no scenario comparison |

### 1.3.3 Competitive Positioning of the Traffic Simulator

| **Feature** | **Traffic Simulator (This Project)** | **PTV Vissim** | **Aimsun** | **Raw SUMO** |
|-------------|--------------------------------------|----------------|------------|--------------|
| **Cost** | Free (Open Source) | ₱500K–₱2M+ | ₱400K–₱1.5M+ | Free |
| **Technical Expertise Required** | Low (Web-based GUI) | High | High | Very High |
| **Philippine Localization** | Yes (7 Bacoor scenarios) | No | No | No |
| **Web-Based Interface** | Yes | No | Limited | No |
| **Real-Time Analytics Dashboard** | Yes | Yes | Yes | No |
| **AI-Powered Recommendations** | Yes | Limited | Yes | No |
| **Multi-Session Support** | Yes | Yes | Yes | Manual only |
| **Accessibility for Non-Technical Users** | High | Low | Low | Very Low |
| **Local Vehicle Types (Jeepney, Tricycle)** | Yes | No | No | Manual configuration |

### 1.3.4 Competitive Advantage

The Traffic Simulator differentiates itself through:

1. **Accessibility**: Web-based interface eliminates the steep learning curve associated with professional tools (ISO 25010 Usability: 4.12/5.00 - Very Good)
2. **Localization**: Pre-configured Philippine traffic scenarios (7 Bacoor City networks) with realistic local vehicle types (jeepneys, tricycles, motorcycles, buses)
3. **Validated Accuracy**: 99.0% average accuracy against real-world BTMD traffic data across 5 validated networks (90.3%-99.9% range)
4. **Cost-Effectiveness**: Zero licensing cost leveraging open-source SUMO engine
5. **Decision Support Focus**: AI-powered recommendations translate simulation data into actionable insights
6. **LGU-Oriented Design**: Tailored for traffic management departments with limited technical resources (Satisfaction & Learnability: 4.38/5.00 - Excellent)
7. **Multi-Session Support**: Concurrent simulation execution with isolated resources and dynamic port allocation

### 1.3.5 SWOT Analysis

| **Strengths** | **Weaknesses** |
|---------------|----------------|
| Free and open-source foundation | Desktop-only deployment (localhost) |
| 99.0% validated accuracy against BTMD data | Limited to 7 pre-configured networks (71.4% validated) |
| User-friendly web interface (ISO 25010: 4.24/5.00) | Requires SUMO installation |
| AI-powered recommendations | No real-time sensor integration |
| Multi-session support with isolated resources | Pre-configured networks only (no custom road builder) |
| Realistic Philippine vehicle types (5 categories) | Based on static data, not live traffic feeds |
| OSM scenario importer for network expansion | Networks must be created externally using SUMO tools |

| **Opportunities** | **Threats** |
|-------------------|-------------|
| Growing smart city initiatives in Philippines | Competition from well-funded commercial tools |
| Government digitalization programs (Build Better More) | Rapid technological changes in AI/ML |
| Academic partnerships for research and education | Budget constraints in LGUs |
| Expansion to other Philippine cities using OSM data | Resistance to technology adoption |
| Integration with traffic sensor systems | Dependence on SUMO engine development |

---

## 1.4 Demand / Need for the System

### 1.4.1 The Philippine Traffic Crisis

The demand for traffic simulation and management tools in the Philippines is driven by a severe urban mobility crisis:

| **Indicator** | **Current Status** | **Source** |
|---------------|-------------------|------------|
| **Daily Economic Loss (Metro Manila)** | ₱3. 5 billion per day | JICA Study, 2024 |
| **Annual Economic Loss** | ₱1.27 trillion | JICA Study, 2024 |
| **Projected Daily Loss by 2035** | ₱5.4 billion (without intervention) | JICA Study, 2024 |
| **Global Congestion Ranking** | #1 Worst Traffic (2023 TomTom Index) | TomTom, 2023 |
| **Average Congestion Level** | 52% | TomTom Traffic Index, 2023 |
| **Annual Hours Lost to Traffic** | 117 hours per commuter | TomTom, 2023 |
| **Rush Hour Travel Speed** | 19 km/h | CPBRD, 2024 |
| **Time to Travel 10 km** | 25-27 minutes average | CPBRD, 2024 |

### 1.4.2 Bacoor City Specific Context

As a rapidly urbanizing city in Cavite province within the CALABARZON region, Bacoor City faces unique traffic challenges. The traffic simulation system has been calibrated and validated using real-world data from the Bacoor Traffic Management Department (BTMD):

| **Factor** | **Description** |
|------------|------------------|
| **Population Growth** | One of the fastest-growing cities in the Philippines |
| **Proximity to Metro Manila** | Major gateway connecting Cavite to NCR |
| **Commercial Development** | Multiple malls (SM Bacoor: 2,823 veh/hr peak; SM Molino: 2,085 veh/hr peak) generating significant traffic |
| **Educational Institutions** | Schools and universities creating periodic congestion |
| **Infrastructure Constraints** | Limited arterial roads; key intersections frequently gridlocked |
| **Current Management Approach** | Manual enforcement; fixed-timer signals; reactive rather than proactive |
| **BTMD Data Validation** | System validated against 5 intersections with 99.0% average accuracy (90.3%-99.9% range) |
| **Network Coverage** | 7 pre-configured traffic scenarios covering major congestion points (71.4% validated) |

### 1. 4.3 Specific Challenges Addressed by the System

| **Challenge** | **Current Situation** | **How the System Addresses It** |
|---------------|----------------------|--------------------------------|
| **Lack of Pre-Implementation Testing** | Traffic interventions are implemented through costly trial-and-error | Enables virtual testing of strategies before real-world deployment |
| **Fixed-Timer Signal Inefficiency** | Most intersections use non-adaptive signals that cannot respond to demand | Provides adaptive signal control simulation and comparison with fixed timing |
| **Absence of Data-Driven Evidence** | Budget requests lack quantitative justification | Generates comprehensive KPI reports and comparative analytics |
| **Inaccessibility of Professional Tools** | Commercial software costs ₱500K–₱2M+ per license | Provides free, web-based access to professional-grade simulation |
| **Limited Technical Expertise** | LGU staff lack SUMO/simulation training | Offers intuitive interface requiring minimal technical knowledge |
| **No Scenario Comparison Capability** | Cannot evaluate multiple strategies simultaneously | Supports multi-session management and comparative analysis |

### 1.4.4 Policy and Institutional Demand

The system aligns with several national initiatives and policies:

| **Initiative** | **Relevance to Traffic Simulator** |
|----------------|-----------------------------------|
| **Build Better More Program** | Supports infrastructure validation through simulation-based planning |
| **Philippine Development Plan 2023-2028** | Addresses transportation and mobility improvement targets |
| **DICT Digital Transformation Agenda** | Contributes to smart city and e-governance initiatives |
| **LGU Modernization Programs** | Provides accessible digital tools for local traffic management |
| **Clean Air Act Implementation** | Enables emissions analysis and environmental impact assessment |
| **DOTr Traffic Management Programs** | Supports data-driven traffic management strategies |

### 1.4. 5 Demand Validation from Stakeholder Engagement

Based on interviews and evaluations with BTMD personnel conducted during the study:

| **Stakeholder Feedback** | **Implication for Demand** |
|--------------------------|---------------------------|
| Traffic enforcers expressed need for tools to evaluate signal timing changes | Direct demand for simulation-based decision support |
| Officers requested evidence-based reports for budget proposals | Validates need for quantitative analytics and export features |
| Lack of existing simulation tools in BTMD operations | Confirms gap in current capabilities that the system fills |
| Difficulty in predicting intervention outcomes | Demonstrates need for predictive simulation capabilities |
| Positive pilot evaluation results: Functionality evaluation (4.16/5.00 - Very Good to Excellent) | Demonstrates user acceptance and perceived utility |
| ISO 25010 evaluation: 4.24/5.00 (Excellent) | Confirms system meets software quality standards |
| BTMD data validation: 5 of 7 networks validated with 99.0% average accuracy | Demonstrates system produces realistic and accurate simulations |

### 1.4. 6 Market Demand Summary

| **Demand Factor** | **Assessment** | **Evidence** |
|-------------------|----------------|--------------||
| **Economic Necessity** | Very High | ₱3.5B daily losses demand cost-effective solutions |
| **Institutional Gap** | High | No existing accessible simulation tools for Philippine LGUs |
| **Policy Alignment** | Strong | Supports national infrastructure and digitalization programs |
| **User Acceptance** | Validated | ISO 25010: 4.24/5.00 (Excellent); Functionality: 4.16/5.00 (Very Good to Excellent) |
| **Data Accuracy** | Validated | 99.0% average accuracy across 5 validated BTMD networks (90.3%-99.9% range) |
| **Scalability Potential** | Moderate-High | Expandable to other cities; OSM import supports new scenarios |
| **Technical Feasibility** | Confirmed | Successfully developed and tested with BTMD; 71.4% network validation coverage |

---

## 1.5 Financial Projections (Potential Revenue Model)

### 1.5.1 Potential Revenue Streams

| **Revenue Stream** | **Description** | **Estimated Value** |
|-------------------|-----------------|---------------------|
| **LGU Licensing** | Annual subscription for municipalities | ₱20,000–₱75,000/year per LGU |
| **Training Workshops** | Hands-on training for traffic personnel | ₱3,000–₱5,000/session |
| **Consulting Services** | Custom scenario development and analysis | ₱10,000–₱50,000/project |
| **Academic Licensing** | Institutional access for universities | ₱5,000–₱15,000/year |
| **Enterprise Solutions** | Custom deployments for large agencies | ₱100,000–₱200,000/year |

### 1.5.2 Break-Even Analysis

| **Cost Category** | **One-Time** | **Annual** |
|-------------------|--------------|------------|
| Development (Completed) | ₱52,000 | — |
| Maintenance & Updates | — | ₱5,000–₱10,000 |
| Hosting (Optional Cloud) | — | ₱12,000–₱24,000 |
| Training Materials | ₱5,000 | ₱2,000 |
| **Total** | **₱57,000** | **₱19,000–₱36,000** |

**Break-Even Point:** 2-3 LGU subscriptions at mid-tier pricing would cover annual operational costs.

---

## 1. 6 Market Feasibility Conclusion

Based on the comprehensive analysis above, the **Traffic Simulator: Analysis and Recommendation of Effect in Traffic Management Strategies** demonstrates **strong market feasibility** for the following reasons:

### 1.6.1 Key Findings

1. **Clear Target Markets**: Well-defined primary (LGUs, traffic authorities) and secondary (academia, researchers) user segments exist with unmet needs

2. **Competitive Differentiation**: The system occupies a unique position—bridging professional simulation capabilities with accessibility and Philippine localization

3. **Demonstrated Demand**: The ₱3.5 billion daily economic loss from traffic congestion creates urgent demand for decision-support tools

4. **Validated Performance**: 
   - **ISO 25010 Evaluation**: 4.24/5.00 (Excellent) - Confirms software quality standards
   - **Functionality Evaluation**: 4.16/5.00 (Very Good to Excellent) - Validates system usability and features
   - **Data Accuracy**: 99.0% average accuracy against BTMD real-world data (5 networks validated)
   - **Network Coverage**: 71.4% of system networks validated (5 of 7)

5. **Sustainable Model**: Open-source foundation with potential for LGU licensing, training services, and academic partnerships

6. **Policy Alignment**: Strong alignment with national digitalization and smart city initiatives (Build Better More, Philippine Development Plan 2023-2028)

### 1.6.2 Feasibility Rating

| **Criteria** | **Rating** | **Justification** |
|--------------|------------|-------------------|
| Market Demand | ⭐⭐⭐⭐⭐ | Severe traffic crisis creates urgent need |
| Competitive Position | ⭐⭐⭐⭐ | Unique value proposition; no direct local competitors |
| Technical Viability | ⭐⭐⭐⭐⭐ | Successfully developed and validated with BTMD data (99.0% accuracy) |
| Financial Sustainability | ⭐⭐⭐⭐ | Low operational costs; multiple revenue streams |
| Data Accuracy | ⭐⭐⭐⭐⭐ | Validated against real-world BTMD data (5 networks, 90.3%-99.9% accuracy) |
| User Acceptance | ⭐⭐⭐⭐⭐ | ISO 25010: 4.24/5.00 (Excellent); Functionality: 4.16/5.00 (Very Good) |
| Scalability | ⭐⭐⭐⭐ | OSM import enables expansion to other cities |
| **Overall Feasibility** | **⭐⭐⭐⭐⭐ (Excellent)** | Validated technical capability with strong market alignment |

### 1.6.3 Recommendations

**Based on validated system performance (ISO 25010: 4.24/5.00; BTMD Data Accuracy: 99.0%), the following deployment recommendations are made:**

1. **Short-Term (0-6 months)**: 
   - Continue pilot deployment with BTMD using validated networks
   - Gather operational feedback on AI-powered recommendations
   - Complete validation of remaining 2 networks (Perpetual Molino, Statesfield)
   
2. **Medium-Term (6-12 months)**: 
   - Expand to 2-3 additional LGUs in Cavite province
   - Develop training materials and workshops for traffic personnel
   - Integrate additional Philippine city networks using OSM importer
   
3. **Long-Term (1-2 years)**: 
   - Develop cloud-based deployment option for wider accessibility
   - Establish academic partnerships for research and education
   - Explore integration with real-time traffic sensor systems
   - Scale to Metro Manila and other CALABARZON cities

---

# SECTION 2: CONTEXT DIAGRAM

## 2.1 Overview

The Context Data Flow Diagram illustrates the system boundary and data exchanges between the Traffic Simulator and its external entities. The system interfaces with two primary user types: Traffic Enforcers (field personnel) and Traffic Officers (planning and policy personnel) from the Bacoor Traffic Management Department (BTMD). 

---

## 2.2 External Entities

### 2.2.1 Entity Descriptions

| **Entity** | **Type** | **Description** | **Role in System** |
|------------|----------|-----------------|-------------------|
| **Traffic Enforcer** | Primary User | Field personnel responsible for on-ground traffic management and data collection | Provides operational data; receives field-relevant simulation outputs |
| **Traffic Officer** | Primary User | Strategic-level personnel responsible for planning and policy decisions | Provides strategic inputs; receives analytical reports and AI-powered recommendations |

### 2.2.2 Entity Characteristics

#### Traffic Enforcer
- **Location**: Field-based (intersections, roads)
- **Technical Expertise**: Low to Moderate
- **Primary Interactions**: Traffic observations; simulation monitoring
- **Key Requirements**: Simple interface; visual outputs; actionable recommendations

#### Traffic Officer
- **Location**: Office-based (BTMD headquarters)
- **Technical Expertise**: Moderate
- **Primary Interactions**: Strategic planning; report generation; policy evaluation
- **Key Requirements**: Comprehensive analytics; export capabilities (CSV/PDF); comparative analysis

---

## 2.3 Context Data Flow Diagram

### 2.3.1 Visual Representation

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                    EXTERNAL ENVIRONMENT                                  │
│                                                                                         │
│    ┌──────────────────────┐                                  ┌──────────────────────┐   │
│    │   TRAFFIC ENFORCER   │                                  │   TRAFFIC OFFICER    │   │
│    │                      │                                  │                      │   │
│    │  • Field Personnel   │                                  │  • Planning Staff    │   │
│    │  • Data Collectors   │                                  │  • Decision Makers   │   │
│    │  • Enforcement Staff │                                  │  • Policy Analysts   │   │
│    └──────────┬───────────┘                                  └───────────┬──────────┘   │
│               │                                                          │              │
│               │ ▼ Traffic Reports                    Strategic Goals ▼   │              │
│               │ ▼ Road Layout Observations           Simulation Params ▼ │              │
│               │ ▼ Control Configurations             Planning Inputs ▼   │              │
│               │                                                          │              │
│               │ ▲ Simulation Visuals                 Analytical Reports ▲│              │
│               │ ▲ Field Analytics                    AI Recommendations ▲│              │
│               │ ▲ Operational Recommendations        KPI Dashboards ▲    │              │
│               │                                      Comparative Data ▲  │              │
│               │                                                          │              │
│    ┌──────────▼──────────────────────────────────────────────────────────▼──────────┐   │
│    │                                                                                 │   │
│    │                              TRAFFIC SIMULATOR:                                 │   │
│    │                                                                                 │   │
│    │              Analysis and Recommendation of Effect in Traffic                   │   │
│    │                         Management Strategies                                   │   │
│    │                                                                                 │   │
│    │  ┌─────────────────────────────────────────────────────────────────────────┐   │   │
│    │  │                         SYSTEM PROCESSES                                 │   │   │
│    │  │                                                                         │   │   │
│    │  │  1.0 Select and Configure Network Scenarios                            │   │   │
│    │  │  2.0 Configure Simulation Parameters                                    │   │   │
│    │  │  3.0 Execute Traffic Simulations (SUMO Engine)                          │   │   │
│    │  │  4.0 Analyze Results and Generate AI Recommendations                    │   │   │
│    │  │  5.0 Generate Visualizations and Reports                                │   │   │
│    │  │  6.0 Manage Multi-Session Concurrent Simulations                        │   │   │
│    │  │                                                                         │   │   │
│    │  └─────────────────────────────────────────────────────────────────────────┘   │   │
│    │                                                                                 │   │
│    │  ┌─────────────────────────────────────────────────────────────────────────┐   │   │
│    │  │                         DATA STORES                                      │   │   │
│    │  │                                                                         │   │   │
│    │  │  • Session Database (SQLite)                                            │   │   │
│    │  │  • BTMD Traffic Data (7 Networks)                                       │   │   │
│    │  │  • Simulation Results Archive                                           │   │   │
│    │  │  • AI Recommendations Repository                                        │   │   │
│    │  │                                                                         │   │   │
│    │  └─────────────────────────────────────────────────────────────────────────┘   │   │
│    │                                                                                 │   │
│    └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                          │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

### 2.3.2 Simplified Context Diagram

```
                              ┌─────────────────────┐
                              │  Traffic Enforcer   │
                              └──────────┬──────────┘
                                         │
                    Traffic Reports ─────┤
                    Road Observations ───┤
                    Control Configs ─────┤
                                         │
                    Simulation Visuals ◄─┤
                    Field Analytics ◄────┤
                    Op. Recommendations ◄┤
                                         ▼
┌───────────────────┐         ┌─────────────────────────────────┐
│  Traffic Officer  │◄───────►│      TRAFFIC SIMULATOR:         │
└───────────────────┘         │                                 │
                              │   Analysis and Recommendation   │
  Strategic Goals ───────────►│   of Effect in Traffic          │
  Simulation Params ─────────►│   Management Strategies         │
  Planning Inputs ───────────►│                                 │
                              │   • SUMO Simulation Engine      │
  Analytical Reports ◄────────│   • AI Recommendation System    │
  AI Recommendations ◄────────│   • Multi-Session Management    │
  KPI Dashboards ◄────────────│   • BTMD Data Integration       │
  Comparative Analytics ◄─────│                                 │
                              └─────────────────────────────────┘
```

---

## 2.4 Data Flow Specifications

### 2.4.1 Traffic Enforcer Data Flows

#### Inbound Flows (Enforcer → System)

| **Data Flow** | **Description** | **Data Elements** | **Frequency** |
|---------------|-----------------|-------------------|---------------|
| **Traffic Reports** | On-ground traffic observations and incident reports | Location; Time; Traffic Volume; Incident Type; Weather Conditions; Vehicle Counts | Daily/As needed |
| **Road Layout Observations** | Physical road configuration data | Lane Counts; Road Width; Junction Type; Signal Presence; Road Markings | As needed |
| **Control Configurations** | Traffic control settings for simulation | Signal Timing; Phase Sequences; Counterflow Schedules; Control Method (Fixed/Adaptive) | Per simulation |

#### Outbound Flows (System → Enforcer)

| **Data Flow** | **Description** | **Data Elements** | **Frequency** |
|---------------|-----------------|-------------------|---------------|
| **Simulation Visuals** | Visual representation of simulated traffic scenarios | Vehicle Animations; Congestion Heatmaps; Signal State Displays; Queue Visualizations | Per simulation |
| **Field Analytics** | Operational metrics relevant to field enforcement | Queue Lengths; Wait Times; Throughput Rates; Congestion Levels | Per simulation |
| **Operational Recommendations** | AI-generated actionable suggestions for implementation | Signal Timing Adjustments; Lane Management; Enforcement Priorities; Expected Impacts | Per analysis |

### 2.4.2 Traffic Officer Data Flows

#### Inbound Flows (Officer → System)

| **Data Flow** | **Description** | **Data Elements** | **Frequency** |
|---------------|-----------------|-------------------|---------------|
| **Strategic Goals** | Long-term traffic management objectives | Target KPIs; Priority Areas; Timeline; Budget Constraints; Policy Guidelines | Per planning cycle |
| **Simulation Parameters** | Configuration settings for simulation runs | Duration (min); Traffic Scale (1x-10x); Vehicle Types; Control Methods; Network Selection (7 options) | Per simulation |
| **Planning Inputs** | Infrastructure and policy proposals for evaluation | Proposed Changes; Alternative Scenarios; Comparison Criteria; Evaluation Metrics | Per project |

#### Outbound Flows (System → Officer)

| **Data Flow** | **Description** | **Data Elements** | **Frequency** |
|---------------|-----------------|-------------------|---------------|
| **Analytical Reports** | Comprehensive simulation analysis documents | KPI Summaries; Trend Analysis; Statistical Comparisons; Executive Summary; CSV/PDF Export | Per simulation |
| **AI Recommendations** | Machine learning-generated traffic improvement suggestions | Priority Actions; Expected Impacts; Implementation Steps; Cost-Benefit Analysis | Per analysis |
| **KPI Dashboards** | Interactive visualization of performance metrics | Average Delay; Throughput; Queue Length; Speed; Emissions; Trip Duration | Real-time/Per simulation |
| **Comparative Analytics** | Multi-scenario comparison results | Side-by-Side Metrics; Ranking Tables; Improvement Percentages; Trade-off Analysis | Per comparison request |

---

## 2.5 Process Descriptions (Level 0)

### 2.5.1 System Processes

| **Process** | **Name** | **Description** | **Inputs** | **Outputs** |
|-------------|----------|-----------------|------------|-------------|
| **1.0** | Select and Configure Network Scenarios | Select from 7 pre-configured Bacoor City networks calibrated with BTMD data | Network Selection; BTMD Traffic Data | Network Configuration (D1) |
| **2.0** | Configure Simulation Parameters | Set up simulation settings: duration, traffic scale, vehicle types, control methods | Simulation Parameters; Strategic Goals | Simulation Configuration (D2) |
| **3.0** | Execute Traffic Simulations | Run SUMO microscopic simulations with configured parameters and multi-session support | Network Config (D1); Simulation Config (D2) | Simulation Results (D3) |
| **4.0** | Analyze Results and Generate AI Recommendations | Process simulation outputs and generate machine learning-based recommendations | Simulation Results (D3) | Analytics & AI Recommendations (D4) |
| **5.0** | Generate Visualizations and Reports | Produce interactive dashboards, charts, and exportable reports (CSV/PDF) | Analytics (D4) | Reports; Visuals; Dashboards |
| **6.0** | Manage Multi-Session Concurrent Simulations | Handle multiple simultaneous simulation sessions with isolated resources | Session Requests; Resource Allocation | Session Management Data |

### 2.5.2 Data Stores

| **Store** | **Name** | **Contents** |
|-----------|----------|--------------|
| **D1** | Network Configuration Repository | 7 pre-configured Bacoor City networks; BTMD traffic data; road geometries; signal timings |
| **D2** | Simulation Configuration Repository | Session parameters; network selections; traffic scale settings; control method configurations |
| **D3** | Simulation Results Archive | SUMO output files (stats.xml, tripinfo.xml, summary.xml); emissions data; timestamped performance metrics |
| **D4** | Analytics & AI Recommendations Store | Generated KPIs; AI-powered recommendations; comparative analysis results; exportable reports (CSV/PDF) |
| **D5** | Session Database (SQLite) | Session metadata; configuration history; trip data; time series metrics; recommendation logs |

---

## 2.6 System Capabilities and Validated Performance

### 2.6.1 Network Coverage and Validation

| **Network** | **Location** | **Calibrated Volume (veh/hr)** | **Validation Status** | **Accuracy** |
|-------------|--------------|--------------------------------|----------------------|--------------|
| SM Bacoor Area | Aguinaldo Hwy & Tirona Hwy | 2,818 | Validated | 99.8% |
| SM Molino Area | Daang Hari Rd & Molino Rd | 2,088 | Validated | 99.9% |
| Jollibee Molino Area | Bacoor Blvd & Molino Rd | 1,490 | Validated | 99.7% |
| St Dominic Area | Bacoor Blvd & Aguinaldo Hwy | 880 | Validated | 90.3% (1x), 99.7% (10x) |
| Bayanan Area | Bacoor Blvd & Bayanan Rd | 761 | Validated | 99.7% |
| Perpetual Molino Area | - | 1,632 | BTMD Average Data | Not yet validated |
| Statesfield Area | - | 1,632 | BTMD Average Data | Not yet validated |

**Overall Coverage:** 71.4% validated (5 of 7 networks)  
**Average Accuracy:** 99.0% across validated networks (range: 90.3%-99.9%)

### 2.6.2 Vehicle Type Support

The system models five Philippine vehicle categories based on BTMD data:

| **Vehicle Type** | **SUMO Classification** | **Calibration Accuracy** |
|------------------|------------------------|--------------------------|
| Passenger Vehicles | `passenger` | 0.1% - 5.0% variance |
| Motorcycles | `motorcycle` | 0.0% - 1.3% variance |
| Trucks | `truck` | 0.0% - 2.2% variance |
| Jeepneys | `bus` (custom parameters) | 0.1% - 1.9% variance |
| Buses | `bus` | 0.0% - 0.2% variance |

**Known Limitation:** Tricycles are mapped to jeepneys due to SUMO classification constraints.

### 2.6.3 Performance Metrics

**System Quality (ISO 25010:2011 Evaluation):**
- Overall Rating: 4.24/5.00 (Excellent)
- Usability: 4.12/5.00 (Very Good)
- Satisfaction & Learnability: 4.38/5.00 (Excellent)
- Reliability & Data Accuracy: 4.20/5.00 (Excellent)
- Performance Efficiency: 4.28/5.00 (Excellent)

**Functionality Evaluation:**
- Overall Rating: 4.16/5.00 (Very Good to Excellent)
- All major modules rated between 4.00 and 4.27

**Speed Ordinance Compliance:**
- Bacoor City Ordinance 227-2022 compliance validated
- Normal conditions (1x): 36.58 km/h (within 30-40 km/h for crowded streets)
- Congested conditions (10x): 21.20-37.26 km/h (realistic speed reduction)

---

## 2.7 Figure Caption

**Figure 2.X** Context Data Flow Diagram

*This context diagram illustrates the interactions between two primary external entities—Traffic Enforcer and Traffic Officer—and the central Traffic Simulator system. The Traffic Enforcer provides operational data including traffic reports, road layout observations, and control configurations, receiving simulation visuals and field-relevant analytics in return. The Traffic Officer supplies strategic goals and simulation parameters, receiving comprehensive analytical reports, AI-powered recommendations, and interactive KPI dashboards. The system operates as a web-based platform integrating SUMO simulation engine, SQLite database for session management, and AI-powered recommendation generation, with all 7 Bacoor City networks calibrated using validated BTMD traffic data.*

---

## 2.8 Data Dictionary for Context Diagram

### 2.8.1 External Entity Attributes

| **Entity** | **Attribute** | **Description** | **Data Type** |
|------------|---------------|-----------------|---------------|
| Traffic Enforcer | enforcer_id | Unique identifier | VARCHAR(20) |
| Traffic Enforcer | name | Full name | VARCHAR(100) |
| Traffic Enforcer | assigned_area | Deployment zone (7 Bacoor networks) | VARCHAR(50) |
| Traffic Enforcer | contact_number | Mobile number | VARCHAR(15) |
| Traffic Officer | officer_id | Unique identifier | VARCHAR(20) |
| Traffic Officer | name | Full name | VARCHAR(100) |
| Traffic Officer | department | BTMD division | VARCHAR(50) |
| Traffic Officer | access_level | System permissions | ENUM(View/Analyze/Admin) |

### 2.8.2 Data Flow Attributes

| **Data Flow** | **Attribute** | **Description** | **Data Type** |
|---------------|---------------|-----------------|---------------|
| Traffic Reports | report_id | Unique report identifier | UUID |
| Traffic Reports | timestamp | Date and time of observation | DATETIME |
| Traffic Reports | location | Intersection name (7 Bacoor networks) | VARCHAR(100) |
| Traffic Reports | vehicle_count | Number of vehicles observed | INTEGER |
| Traffic Reports | congestion_level | Subjective assessment | ENUM(Low/Medium/High/Severe) |
| Simulation Parameters | session_id | Unique simulation session identifier | UUID |
| Simulation Parameters | duration | Simulation length in minutes | INTEGER |
| Simulation Parameters | traffic_scale | Traffic intensity multiplier (1x-10x) | FLOAT |
| Simulation Parameters | control_method | Signal control type | ENUM(Fixed/Adaptive/Existing) |
| Simulation Parameters | network_selection | Selected Bacoor network | ENUM(7 network options) |
| AI Recommendations | recommendation_id | Unique recommendation identifier | UUID |
| AI Recommendations | priority_level | Urgency of action | ENUM(High/Medium/Low) |
| AI Recommendations | expected_impact | Projected improvement percentage | FLOAT |
| AI Recommendations | implementation_cost | Estimated resource requirement | VARCHAR(50) |

### 2.8.3 BTMD Network Attributes

| **Network** | **Attribute** | **Description** | **Data Type** |
|-------------|---------------|-----------------|---------------|
| All Networks | network_id | Unique network identifier | VARCHAR(50) |
| All Networks | calibrated_volume | Target vehicles per hour from BTMD data | INTEGER |
| All Networks | validation_status | Whether validated against BTMD measurements | ENUM(Validated/Averaged/Pending) |
| All Networks | accuracy_percentage | Validation accuracy (if validated) | FLOAT |
| All Networks | vehicle_mix | Distribution of 5 vehicle types | JSON |
| All Networks | peak_hour | Time of maximum traffic (BTMD data) | TIME |

---

# REFERENCES

## Market Feasibility Study References

1. Business Research Insights. (2024). *Traffic Simulation Systems Market Size, Growth & Forecast, 2035*. Retrieved from https://www.businessresearchinsights.com/market-reports/traffic-simulation-systems-market-114288

2. Congressional Policy and Budget Research Department (CPBRD). (2024). *Traffic Congestion in Metro Manila Facts*. Retrieved from https://cpbrd.congress.gov.ph/

3. DataIntelo. (2024). *Traffic Simulation Systems Market Report | Global Forecast From 2025 To 2033*. Retrieved from https://dataintelo.com/report/traffic-simulation-systems-market

4. Department of Finance (DOF). (2024). *Opening Remarks: Metro Manila Subway Project (MMSP) Worksite Visit and Press Briefing*. Retrieved from https://www.dof.gov.ph/

5. East Asia Forum. (2025). *Unlocking sustainable mobility in Metro Manila*. Retrieved from https://eastasiaforum.org/

6. Growth Market Reports. (2024). *Traffic Simulation Software Market Research Report 2033*. Retrieved from https://growthmarketreports.com/report/traffic-simulation-software-market

7. Gulf News. (2024). *Why is Manila traffic the worst in the world? Here's how to solve it*. Retrieved from https://gulfnews.com/

8. Kings Research. (2024). *Traffic Simulation Systems Market Size Share & Growth, 2032*. Retrieved from https://www.kingsresearch.com/traffic-simulation-systems-market-24

9. Manila Bulletin. (2024). *Metro Manila subway to prevent ₱2.5 billion in traffic-related losses*. Retrieved from https://mb.com.ph/

10. Manila Standard. (2024). *Vehicular traffic challenges*. Retrieved from https://manilastandard.net/

11. ReportPrime. (2024). *Traffic Simulation Software Market Size, Growth, Forecast Till 2031*. Retrieved from https://www.reportprime.com/traffic-simulation-software-r13281

12. The Daily Tribune. (2024). *₱3.5-B daily traffic losses*. Retrieved from https://tribune.net.ph/

13. The LaSallian. (2024). *The urban costs of the Philippines' car obsession*. Retrieved from https://thelasallian.com/

14. TomTom. (2023). *TomTom Traffic Index 2023*. Retrieved from https://www.tomtom.com/traffic-index/

15. Verified Market Reports. (2024). *Traffic Simulation Software Market Size, Insights, SWOT & Competitive Analysis*. Retrieved from https://www.verifiedmarketreports.com/

16. WiseGuy Reports. (2024). *Traffic Simulation Software Market Size & Future Growth 2035*. Retrieved from https://www.wiseguyreports.com/

## Thesis and System Documentation References

17. Bacoor Traffic Management Department (BTMD). (2025). *Vehicle Count Data - Bacoor City Intersections*. Unpublished raw data.

18. Eclipse SUMO Documentation. (2024). *Simulation of Urban MObility User Documentation*. Retrieved from https://sumo.dlr.de/docs/

19. International Organization for Standardization. (2011). *ISO/IEC 25010:2011 Systems and software engineering - Systems and software Quality Requirements and Evaluation (SQuaRE)*. Geneva: ISO.

20. Republic of the Philippines - Bacoor City. (2022). *City Ordinance No. 227-2022: Speed Limit Ordinance*. Bacoor City Local Government.

---

**Document Information:**
- **Project:** Traffic Simulator: Analysis and Recommendation of Effect in Traffic Management Strategies
- **Institution:** University of Perpetual Help System-DALTA-Molino Campus
- **Program:** Bachelor of Science in Information Technology
- **Course:** Capstone Project
- **Academic Year:** 2024-2025
- **Date:** December 2025
- **Version:** 2.0 (Revised - Aligned with Thesis Chapters 3 & 4)
- **Status:** Validated System with BTMD Data (99.0% Average Accuracy across 5 Networks)