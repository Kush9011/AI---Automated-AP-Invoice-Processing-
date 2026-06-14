import os
import json
from backend.ai_service import extract_invoice


def load_text_from_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def main():
    # 👇 change this to your local file path
    file_path = r"C:\Users\kush2\Downloads\ap-ai-system\sample_invoice.txt"

    if not os.path.exists(file_path):
        print("❌ File not found:", file_path)
        return

    print("📄 Reading file...")
    text = load_text_from_file(file_path)

    print("🤖 Sending to AI service...\n")
    result = extract_invoice(text)

    print("\n================ AI OUTPUT ================\n")

    try:
        parsed = json.loads(result)
        print(json.dumps(parsed, indent=4))
    except Exception:
        print("⚠️ Raw output (not valid JSON):\n")
        print(result)


if __name__ == "__main__":
    main()