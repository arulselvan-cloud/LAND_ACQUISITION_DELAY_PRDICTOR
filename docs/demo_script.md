# LandSight AI — Live Demonstration & Evaluation Script

**Problem Statement**: SIH26017 (Ministry of Statistics and Programme Implementation)  
**Platform**: LandSight AI Decision-Support Dashboard  
**Total Target Time**: 4 Minutes 30 Seconds (strictly under 5 minutes)  

---

### Segment 1: The Problem Framing (0:00 – 0:30)
**Visual**: Open the LandSight AI Dashboard homepage (`http://localhost:5173`). The top executive KPI cards, calibrated risk breakdown donut chart (1,225 Low / 1,050 Medium / 700 High / 525 Critical), and interactive national district heatmap are displayed.

**Presenter Narration**:
> *"Respected jury members, over 60% of India's mega infrastructure projects face severe time and cost overruns. The number one culprit is not engineering or finance—it is **land acquisition delays** under the RFCTLARR Act, 2013.*  
> 
> *Right now, monitoring is entirely reactive: District Collectors and Ministry officers only find out a project is paralyzed months after deadlines have already lapsed.*  
> 
> *We built **LandSight AI** to fundamentally shift governance from reactive post-mortems to **predictive early detection and prescriptive intervention** across 3,500 projects spanning 12 Indian states."*

---

### Segment 2: Deep Dive into a Critical Bottleneck — CBIC Package 2 (0:30 – 1:45)
**Visual**: On the dashboard, click on the **Priority Delay Alerts** feed card or search `CBIC-TN-PKG02` in the project catalog. Click the row to slide open the **5-Stage Pipeline Detail Drawer**.

**Presenter Narration**:
> *"Let us look at a real showcase project: the **Chennai-Bengaluru Industrial Corridor (CBIC) Package 2**, an expressway stretch in Ranipet, Tamil Nadu spanning 340.5 hectares and 420 project-affected families.*  
> 
> *In **Stage 1 (Land Data)**, we track the statutory milestone lifecycle: Notification, Survey, Compensation, Possession, and Rehabilitation.*  
> 
> *In **Stage 2 (AI Prediction)**, our trained XGBoost classifier immediately flags CBIC as **CRITICAL RISK** with a **99.35% delay probability**. But prediction alone isn't enough—administrators need to know **why**.*  
> 
> *Moving to **Stage 3 (Explainability Engine)**, our local SHAP TreeExplainer isolates the exact root-cause drivers with mathematical attribution. Notice the top driver: `has_active_legal_dispute` with a **+1.65 log-odds impact**, coupled with a **90-day legal dispute delay**. Crucially, our model also shows mitigating assets—for example, stakeholder responsiveness is at 77.2, which is decreasing risk by -0.58.*  
> 
> *Now look at **Stage 4 (Impact Map)**: Land acquisition is a sequential dependency chain. A 165-day bottleneck in Compensation doesn't stay in Compensation; our autoregressive delay propagation models project it downstream, causing an additional 84 days of delay in physical Possession."*

---

### Segment 3: Live Counterfactual Simulation ("What-If" Engine) (1:45 – 2:45)
**Visual**: Scroll to **Stage 5 (Interactive Intervention Simulator)**. Show the Baseline State vs Counterfactual State side-by-side.

**Presenter Narration**:
> *"This brings us to our most powerful capability: **the What-If Counterfactual Simulator**.  
> Instead of guessing how to unblock the project, an administrator can simulate policy interventions in real time.*  
> 
> *Watch what happens when we intervene on screen:*  
> 1. *We toggle OFF the **Active Court Injunction / Stay Order**.*  
> 2. *We slide **Compensation Disbursement Rate** from 58% up to 95%.*  
> 3. *We increase **Stakeholder Responsiveness** to 90.*  
> 
> *In under 50 milliseconds, our Cox Proportional Hazards and gradient boosting models recalculate the future trajectory:*  
> *The delay risk plummets from **99.35% (CRITICAL)** all the way down to **2.85% (LOW)**.*  
> *And look at the quantified statutory impact banner below: **We save 102 statutory delay days**—18 days saved in Compensation and 84 days saved in physical Possession handover! That represents crores of rupees saved in escalated interest and contractor idling penalties."*

---

### Segment 4: Generative AI Administrative Action Plan (2:45 – 3:45)
**Visual**: Scroll to **Stage 6 (Recommended Administrative Directives & AI Action Memo)**. Point to the blue stylized Gemini Action Memo box and the prioritized action directive cards.

**Presenter Narration**:
> *"Knowing how many days can be saved still leaves the question: **What specific statutory steps must the District Collector take right now?**  
> 
> *LandSight AI bridges analytics directly into executive administration using **Google Gemini 2.5 Flash** grounded in our SHAP explainability drivers.*  
> 
> *Here is the synthesized administrative memo addressed directly to the District Collector and SLAO:*  
> - **Sentence 1 (Root Cause)**: Cites exact project figures: the 99.3% delay risk, 90-day stay order impact, 340.5 hectares, and 420 PAFs.  
> - **Sentence 2 (Directive)**: Mandates the Legal Cell to file an urgency memo in the Madras High Court to vacate the stay, deploys additional revenue surveyor teams for boundary demarcation, and convenes Special Gram Sabhas for PAF grievance redressal.  
> - **Sentence 3 (Timeline & Impact)**: Sets a strict 14-to-30 day operational turnaround under RFCTLARR 2013 to save 60 to 90 days.  
> 
> *Notice our SHAP factor partitioning: Gemini strictly targets **only risk-increasing bottlenecks**. It never erroneously penalizes mitigating strengths like stakeholder responsiveness. And if the LLM API ever times out, our zero-failure fallback guarantees that deterministic administrative templates are returned instantaneously."*

---

### Segment 5: The Contrast Case — Bengaluru Suburban Rail Project (3:45 – 4:15)
**Visual**: Close the CBIC drawer. In the table or heatmap, click on **`BSRP-KA-CORR04`** (Bengaluru Suburban Rail Project - Corridor 4). The drawer opens displaying a **LOW RISK (Green)** badge.

**Presenter Narration**:
> *"To prove that our models are discriminative and not just crying wolf, let us look at **BSRP Corridor 4 in Bengaluru Urban**.*  
> 
> *The model classifies this project as **LOW RISK** with just a **1.6% delay probability**.*  
> *Why? Compensation disbursement is at 94.4%, stakeholder responsiveness is an exceptional 91 out of 100, and there are zero active stay orders.*  
> *Notice that LandSight AI does not flood the administrator with false alarms. Instead of critical alerts, it generates routine milestone monitoring directives to maintain positive acquisition momentum."*

---

### Segment 6: Closing Statement & The 3 Core Differentiators (4:15 – 4:45)
**Visual**: Return to the main national dashboard with the district heatmap and executive overview.

**Presenter Narration**:
> *"To summarize, LandSight AI answers the three critical questions that existing infrastructure dashboards fail to answer:*  
> 1. **Why is the project delayed?** Answered through transparent, local SHAP explainability—not black-box scores.  
> 2. **What happens next if we do nothing?** Answered through sequential milestone delay propagation modeling.  
> 3. **What should the administration do right now?** Answered through interactive What-If simulation and Gemini-powered administrative directives grounded in RFCTLARR 2013.  
> 
> *With LandSight AI, infrastructure monitoring moves from retrospective reports to forward-looking, proactive governance.*  
> *Thank you, and we welcome your questions."*
