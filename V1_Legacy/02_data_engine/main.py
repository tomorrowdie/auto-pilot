import os
import config
from processors import source_1_cerebro

def main():
    print("🚀 Starting Omni Data Engine...")
    print(f"📂 Output Target: {config.REPORT_FILE}")
    
    # --- PHASE 1: PROCESS CEREBRO ---
    candidates = source_1_cerebro.process_cerebro_data(config.DATA_SOURCE_1_PATH)
    
    if candidates:
        report_content = "# Omni Strategy Candidates Report\n\n"
        report_content += source_1_cerebro.generate_report_section(candidates)
        
        # Ensure directory exists
        if not os.path.exists(config.OUTPUT_DIR):
            os.makedirs(config.OUTPUT_DIR)
            
        # Write File
        with open(config.REPORT_FILE, "w", encoding="utf-8") as f:
            f.write(report_content)
        print(f"✅ DONE. Strategy Menu created at: {config.REPORT_FILE}")
        print("👉 Open the file and mark your [x] selections.")
    else:
        print("⚠️ No candidates generated. Check your CSV path or filters.")

if __name__ == "__main__":
    main()