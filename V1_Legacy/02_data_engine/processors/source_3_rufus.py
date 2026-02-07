import json
import os


def load_json(file_path):
    if not os.path.exists(file_path):
        return {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}


def load_review_keywords(happy_path):
    """Extracts keywords from the Happy Flow for comparison."""
    if not os.path.exists(happy_path):
        return []

    try:
        with open(happy_path, 'r', encoding='utf-8') as f:
            data = json.loads(f.read())
            keywords = []
            for item in data:
                kws = item.get('rufus_keywords', '').split(',')
                keywords.extend([k.strip().lower() for k in kws if k.strip()])
            return keywords
    except:
        return []


def process_rufus_intelligence(vision_path, happy_path, defect_path):
    print(f"   [Source 3] Processing Rufus Intelligence...")

    # 1. Load Inputs
    vision_data = load_json(vision_path)
    customer_keywords = load_review_keywords(happy_path)

    # 2. Extract Amazon's Tags
    amazon_tags = [t.lower() for t in vision_data.get('amazon_specific_tags', [])]

    strategy = {
        "kill_decision": "FIX (Do Not Kill)",  # Default logic, can be enhanced
        "marketing_hooks": [],
        "trap_questions": [],
        "defense_plan": []
    }

    # --- LOGIC A: GAP ANALYSIS (Marketing Hooks) ---
    # Find things Customers love (Happy) that Amazon also sees (Vision)
    for tag in amazon_tags:
        if any(tag in k for k in customer_keywords):
            strategy["marketing_hooks"].append({
                "tag": tag.title(),
                "insight": f"High Alignment: Amazon tags '{tag}' and customers confirm it.",
                "action": "Double Down: Use in Title and Sponsored Brand Video."
            })

    # --- LOGIC B: THE TRAP (Missing Tags) ---
    # Check for critical keywords missing from Amazon's vision
    critical_checks = ['travel', 'gift', 'safe', 'durable']
    for check in critical_checks:
        if any(check in k for k in customer_keywords) and check not in amazon_tags:
            strategy["trap_questions"].append({
                "dimension": "Contextual Gap",
                "question": f"Is this product suitable for {check}?",
                "goal": f"Force index: Amazon missed '{check}' tag despite customer mentions."
            })

    # --- LOGIC C: DEFENSE (From Defect Flow) ---
    # (We reuse the defect logic but frame it for Rufus Defense)
    # Placeholder for simple logic: if defects exist, create defense bullets

    # Hardcoded 'Trap Questions' based on 6 Dimensions (The Standard Probe)
    strategy["trap_questions"].extend([
        {"dimension": "1. Precision", "question": "What specific material is the liner made of?",
         "goal": "Verify Material Accuracy"},
        {"dimension": "4. Occasion", "question": "Who is the ideal recipient for this item?",
         "goal": "Check Persona Graph"}
    ])

    return strategy


def generate_report_section(strategy):
    lines = []
    lines.append("## 🤖 Phase 3: Rufus Intelligence (Source 3)")
    lines.append(f"> **Verdict:** **{strategy['kill_decision']}**\n")

    # 1. Marketing Alignment
    if strategy['marketing_hooks']:
        lines.append("### 📢 Validated Marketing Hooks (Amazon + Customer)")
        for item in strategy['marketing_hooks']:
            lines.append(f"* **{item['tag']}**: {item['action']}")
        lines.append("")

    # 2. The Interrogation
    lines.append("### 🕵️ Rufus Interrogation Plan (Trap Questions)")
    lines.append("*Ask these questions to 'Force Index' missing attributes:*")
    for q in strategy['trap_questions']:
        lines.append(f"* [ ] **{q['question']}** ({q['dimension']})")
        lines.append(f"  * *Goal:* {q['goal']}")

    lines.append("")
    return "\n".join(lines)