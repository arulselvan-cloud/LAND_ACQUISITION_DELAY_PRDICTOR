# LandSight AI - Data Assumptions & Distribution Specification (SIH26017)

## 1. Statutory Context & Legal Grounding
The synthetic dataset generation for **LandSight AI** is grounded in the statutory workflows and empirical failure modes of the **Right to Fair Compensation and Transparency in Land Acquisition, Rehabilitation and Resettlement Act, 2013 (RFCTLARR Act 2013)** and complementary state acquisition enactments (e.g., KIADB Act, Tamil Nadu Highway Act, Maharashtra PESA rules).

---

## 2. Project Distribution Assumptions

### 2.1 Project Types
Infrastructure projects are distributed according to national capital expenditure profiles:
- **Highways / Expressways (NHAI, State PWD)**: ~35%
- **Railways & Metro Transit (MoR, DFCCIL, Metro Rail)**: ~25%
- **Industrial Corridors & SEZs (CBIC, DMIC, State SIPCOT/MIDC)**: ~15%
- **Irrigation & Water Resources (Multipurpose Dams, Canals)**: ~15%
- **Urban Infrastructure (Airport expansions, Ring Roads, Ring Lines)**: ~10%

### 2.2 Geographic Spread & Administrative Hierarchy
Projects span 12 major Indian states with diverse geographic, socio-economic, and legal characteristics:
- **Southern Corridor**: Tamil Nadu (`TN`), Karnataka (`KA`), Andhra Pradesh (`AP`), Telangana (`TS`), Kerala (`KL`)
- **Western Industrial Belt**: Maharashtra (`MH`), Gujarat (`GJ`), Rajasthan (`RJ`)
- **Northern / Central Corridor**: Uttar Pradesh (`UP`), Madhya Pradesh (`MP`), Bihar (`BR`)
- **Eastern Resource Zone**: Odisha (`OD`), West Bengal (`WB`)

Each project is assigned to a specific district with realistic WGS84 coordinates (WKT `POINT(longitude latitude)`) clustered within the administrative boundaries of the designated revenue district.

### 2.3 Land Area & Affected Families Distribution
- **Land Area (Hectares)**: Follows a log-normal distribution with $\mu = 4.2, \sigma = 0.85$, bounded between 5.0 and 1,800.0 hectares (median ~65 ha). Large irrigation and highway projects exhibit long right tails.
- **Affected Families Count**: Modeled as a function of project type density and land area:
  - Urban Infra / Metro: High family density per hectare (6.0 - 15.0 families/ha)
  - Highway / Railway: Linear corridor density (1.5 - 4.5 families/ha)
  - Industrial / Irrigation: Dispersed rural density (0.8 - 2.5 families/ha)
  - Long right tail added for densely populated peri-urban clusters.

---

## 3. Statutory Milestones & 5 Lifecycle Stages

Under RFCTLARR 2013, every acquisition project is tracked across 5 discrete statutory milestones:

| Stage Name | Statutory Milestone (RFCTLARR 2013) | Planned Duration (Days) | Typical Bottlenecks |
| :--- | :--- | :--- | :--- |
| **1. Notification** | Section 11 Preliminary Notification & Social Impact Assessment (SIA) | 45 – 90 days | Lapsed 12-month SIA validity window, gazette publication delays |
| **2. Survey** | Section 12 Cadastral Survey & Section 15 Hearing of Objections | 60 – 120 days | Inaccurate land records, boundary disputes, revenue staff shortages |
| **3. Compensation** | Section 19 Declaration & Section 23/30 Final Award Determination | 90 – 180 days | Valuation multiplier disputes, 100% solatium conflict, consent failures |
| **4. Possession** | Section 38 Physical Possession & Eviction | 60 – 120 days | High Court stay orders, violent local resistance, crop removal delay |
| **5. Rehabilitation** | Section 16–18 / 31 Resettlement & Rehabilitation (R&R) Scheme | 120 – 240 days | Delayed township construction, alternate agricultural land unavailability |

---

## 4. Delay Correlation & Empirical Risk Formulations

Total project delays are synthesized using a multi-factor structural causal model where delays are correlated with observable project signals:

$$ \text{Total Delay} = \text{Delay}_{\text{baseline}} + \Delta_{\text{litigation}} + \Delta_{\text{compensation}} + \Delta_{\text{stakeholders}} + \Delta_{\text{tribal\_pesa}} + \Delta_{\text{families}} $$

### 4.1 Legal Disputes & Litigation ($\Delta_{\text{litigation}}$)
- **Probability**: ~25% of projects have active legal challenges (High Court Writ Petitions, Civil Court Partition Suits, LARR Authority references).
- **Stay Orders**: ~45% of active disputes carry judicial stay orders (`stay_order_active = True`).
- **Impact**: Adds **+90 to +720 days** of delay directly halting physical possession and compensation awards.

### 4.2 Compensation Disbursement Deficit ($\Delta_{\text{compensation}}$)
- **Disbursement Distribution**: Follows a Beta distribution ($\alpha = 3.5, \beta = 2.5$) centered between 40% and 80% disbursed.
- **Impact**: Projects where disbursement rate is below 50% experience an added delay of **+60 to +400 days**, driven by landowner refusal to surrender possession until full monetary award realization.

### 4.3 Stakeholder Responsiveness ($\Delta_{\text{stakeholders}}$)
- Each project tracks 2–3 institutional stakeholders (District Collector, Land Acquisition Officer, Implementing Agency, Panchayat).
- Each stakeholder has a responsiveness rating on a scale of 0 to 100.
- **Impact**: When the average stakeholder responsiveness drops below 60, administrative latency contributes **+30 to +200 days** of delay.

### 4.4 Tribal Rights & PESA Clearance ($\Delta_{\text{tribal\_pesa}}$)
- **Probability**: ~15% of projects (concentrated in Fifth Schedule tribal areas in Palghar, Odisha, Rajasthan, and Madhya Pradesh).
- **Impact**: Mandatory Gram Sabha consensus failures under the PESA Act introduce **+60 to +360 days** of statutory stagnation.

### 4.5 High Affected Population Burden ($\Delta_{\text{families}}$)
- When `affected_families_count` exceeds 300 families, the complexity of grievance redressal, consensus-building, and physical relocation contributes **+20 to +150 days**.

---

## 5. Delay Risk Categorization & Saturated Multi-Factor Formulation

Rather than unbounded additive accumulation, delay probabilities and risk classifications are synthesized using a **saturating logistic/sigmoid formulation**:

$$ z = w_0 + w_{\text{dispute}} x_{\text{dispute}} + w_{\text{comp}} x_{\text{comp}} + w_{\text{stk}} x_{\text{stk}} + w_{\text{pesa}} x_{\text{pesa}} + w_{\text{fam}} x_{\text{fam}} + \epsilon $$
$$ \text{Risk Score} = \sigma(z) = \frac{1}{1 + e^{-z}} $$

### 5.1 Percentile-Based Risk Calibration
Risk categories are mapped by calibrated percentiles of the continuous score distribution, ensuring realistic monotonic proportions without threshold collapse:
- **Low Risk** ($\le 35\text{th}$ percentile, ~35% of dataset): Typical delays **0 – 35 days**. High stakeholder responsiveness (>75), no judicial stays, >80% compensation disbursed.
- **Medium Risk** ($35\text{th} - 65\text{th}$ percentile, ~30% of dataset): Typical delays **36 – 95 days**. Moderate disbursement gaps or minor administrative friction.
- **High Risk** ($65\text{th} - 85\text{th}$ percentile, ~20% of dataset): Typical delays **96 – 220 days**. Substantial valuation disputes, slower R&R progression.
- **Critical Risk** ($> 85\text{th}$ percentile, ~15% of dataset): Typical delays **221 – 700+ days**. Active High Court stay orders, tribal PESA deadlock, or low institutional responsiveness.
