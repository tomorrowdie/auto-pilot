import json
import os

def load_json_from_txt(file_path):
    """Reads a text file containing a JSON string."""
    print(f"   [Source 2] Loading: {file_path}")
    if not os.path.exists(file_path):
        print(f"   [Error] File not found: {file_path}")
        return []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            return json.loads(content)
    except Exception as e:
        print(f"   [Error] JSON Parse Failed: {e}")
        return []

def process_reviews(happy_path, defect_path):
    """
    Ingests Happy/Defect flows to build the Rufus Strategy.
    """
    happy_data = load_json_from_txt(happy_path)
    defect_data = load_json_from_txt(defect_path)
    
    rufus_strategy = {
        "context_seeds": [],    # From Happy Flow (Dimension 3)
        "defense_hooks": [],    # From Defect Flow (Addressing Risks)
        "intents": []           # From Cosmo Intents
    }

    # 1. Process Happy Flow (The "Why Buy")
    for item in happy_data:
        # Extract Rufus Keywords (Comma separated string)
        raw_keywords = item.get('rufus_keywords', '')
        if raw_keywords:
            seeds = [k.strip() for k in raw_keywords.split(',') if k.strip()]
            rufus_strategy["context_seeds"].extend(seeds)
            
        # Extract Cosmo Intents (Bullets)
        raw_intents = item.get('cosmo_intents', '')
        if raw_intents:
            # Clean up bullet points
            lines = [line.strip().replace('• ', '') for line in raw_intents.split('\n') if '•' in line]
            rufus_strategy["intents"].extend(lines)

    # 2. Process Defect Flow (The "Why Return")
    for item in defect_data:
        issue = item.get('issue', '')
        tag = item.get('risked_system_tag', '')
        
        # Only list significant issues
        if issue and tag:
            rufus_strategy["defense_hooks"].append({
                "issue": issue,
                "tag": tag
            })

    return rufus_strategy

def generate_report_section(strategy_data):
    lines = []
    lines.append("## 🤖 Source 2: Rufus & Review Intelligence")
    lines.append("> **Context:** Rufus answers customer questions based on Review Sentiment. Use these insights to seed your Q&A and bullets.\n")
    
    # Section A: Contextual Seeds (Happy Flow)
    lines.append("### ✅ Positive Context (Rufus Keywords)")
    lines.append("*These terms appear in positive reviews. Use them to trigger 'Best for...' recommendations.*")
    
    # Deduplicate and take top 15
    unique_seeds = sorted(list(set(strategy_data['context_seeds'])))[:15]
    for seed in unique_seeds:
        lines.append(f"* [ ] `Dim 3` **{seed}**")
    lines.append("\n")

    # Section B: User Intents (Scenarios)
    lines.append("### 🎯 Usage Scenarios (Cosmo Intents)")
    lines.append("*Target these specific use-cases in your 'Who is this for?' section.*")
    
    unique_intents = sorted(list(set(strategy_data['intents'])))[:10]
    for intent in unique_intents:
        lines.append(f"* [ ] **{intent}**")
    lines.append("\n")

    # Section C: Defense Hooks (Defect Flow)
    lines.append("### 🛡️ Defense Strategy (Risk Mitigation)")
    lines.append("*Address these top complaints in your Q&A to prevent Rufus from flagging your product as 'Risky'.*")
    
    for hook in strategy_data['defense_hooks'][:5]: # Top 5 Issues
        lines.append(f"* **Risk:** {hook['issue']}")
        lines.append(f"  * *Action:* Add Q&A addressing `{hook['tag']}`")
    
    lines.append("\n")
    return "\n".join(lines)