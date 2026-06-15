import json
import sys

def generate_markdown(result):
    arbiter = result.get("arbiter", {})
    verdict = arbiter.get("verdict", "UNKNOWN")
    risk_score = arbiter.get("risk_score", 0)
    
    color_map = {
        "SHIP": "Success",
        "WARN": "Warning",
        "STAGE": "Notice",
        "BLOCK": "Critical Risk"
    }
    
    status_text = color_map.get(verdict, "Unknown")
    
    md = [
        f"## HELIOS Config Safety Analysis",
        f"",
        f"**Verdict:** {verdict} ({status_text})  <br/>",
        f"**Risk Score:** {risk_score}/100  <br/>",
        f"**Config File:** {result.get('request', {}).get('config_file', 'unknown')}  <br/>",
        f"**Environment:** {result.get('request', {}).get('environment', 'unknown')}",
        f"",
        f"### Executive Summary",
        f"{arbiter.get('summary', 'No summary provided.')}",
        f"",
        f"### Agent Reasoning Chain",
        f"| Agent | Finding |",
        f"|-------|---------|"
    ]
    
    agents = ["sentinel", "chronicle", "meridian", "context", "oracle"]
    for agent in agents:
        reasoning = arbiter.get(f"reasoning_{agent}", "").replace('\n', ' ')
        if reasoning:
            md.append(f"| **{agent.upper()}** | {reasoning} |")
            
    steps = arbiter.get("remediation_steps", [])
    if steps:
        md.append(f"")
        md.append(f"### Required Remediation")
        for step in steps:
            owner = f" (Owner: {step.get('who')})" if step.get('who') else ""
            md.append(f"{step.get('step_number')}. **{step.get('action')}**{owner}")
            md.append(f"   *Rationale: {step.get('rationale')}*")
            
    return '\n'.join(md)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python format_pr_comment.py <result_json_path>")
        sys.exit(1)
        
    try:
        with open(sys.argv[1], "r", encoding="utf-8") as f:
            content = f.read()
            
        # The true JSON result always starts with { and contains "eval_id"
        # We find the last occurrence of '{' that precedes '"eval_id"'
        # Or even simpler:
        json_start = content.find('{\n  "eval_id":')
        if json_start == -1:
            json_start = content.find('{"eval_id":')
            
        if json_start != -1:
            # The JSON goes to the end of the file
            json_str = content[json_start:]
            # Ensure we only parse until the last closing brace in case of trailing chars
            json_end = json_str.rfind('}') + 1
            data = json.loads(json_str[:json_end])
            print(generate_markdown(data))
        else:
            print("## HELIOS Analysis Failed\nCould not parse evaluation results.")
    except Exception as e:
        print(f"## HELIOS Analysis Error\n{str(e)}")
