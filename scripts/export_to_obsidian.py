import json
import os
import glob
import re
from pathlib import Path

def sanitize_filename(name):
    # Windows doesn't allow certain characters in filenames
    return re.sub(r'[\\/*?:"<>|]', "", name)

def main():
    base_dir = Path(r"c:\Users\badar\PycharmProjects\copa-hackathon\copa-hackathon")
    index_path = base_dir / "data" / "artifacts" / "clause-index.json"
    artifacts_dir = base_dir / "data" / "artifacts"
    obsidian_dir = base_dir / "data" / "obsidian_vault"
    
    if not index_path.exists():
        print(f"Error: {index_path} not found.")
        return

    obsidian_dir.mkdir(parents=True, exist_ok=True)
    print(f"Generating Obsidian vault at {obsidian_dir}...")

    with open(index_path, "r", encoding="utf-8") as f:
        clause_index = json.load(f)

    # Collect connections from trace files
    connections_map = {}
    trace_files = glob.glob(str(artifacts_dir / "connection-trace-*.json"))
    for tf in trace_files:
        try:
            with open(tf, "r", encoding="utf-8") as f:
                trace_data = json.load(f)
                
            findings = trace_data.get("critic_output") or trace_data.get("finder_output") or []
            for finding in findings:
                sources = finding.get("source_clauses", [])
                targets = finding.get("target_clauses", [])
                for src in sources:
                    for tgt in targets:
                        # Link src to tgt
                        connections_map.setdefault(src, set()).add(tgt)
                        # Link tgt to src (bidirectional for graph view)
                        connections_map.setdefault(tgt, set()).add(src)
        except Exception as e:
            print(f"Error processing {tf}: {e}")

    for clause_id, entry in clause_index.items():
        filename = sanitize_filename(clause_id) + ".md"
        filepath = obsidian_dir / filename
        
        content = []
        content.append(f"# {clause_id}")
        
        # Metadata block for Obsidian
        content.append("---")
        content.append(f"policy_id: {entry.get('policy_id')}")
        content.append(f"document_id: {entry.get('document_id')}")
        if entry.get('heading'):
            content.append(f"heading: {entry.get('heading')}")
        content.append("---")
        content.append("")
        
        # Link to Parent
        if entry.get("parent"):
            content.append(f"**Parent:** [[{entry['parent']}]]")
            content.append("")

        # Link to Children
        children = entry.get("children", [])
        if children:
            content.append("**Children:**")
            for child in children:
                content.append(f"- [[{child}]]")
            content.append("")
            
        # Cross-workstream / cross-document connections
        related = connections_map.get(clause_id, set())
        if related:
            content.append("**Related (from AI traces):**")
            for rel in sorted(list(related)):
                content.append(f"- [[{rel}]]")
            content.append("")
            
        # The actual text
        content.append("## Text")
        content.append(entry.get("text", ""))
        
        with open(filepath, "w", encoding="utf-8") as md_file:
            md_file.write("\n".join(content))

    print(f"Done! Created {len(clause_index)} markdown files in {obsidian_dir}.")
    print("You can now open this folder as a Vault in Obsidian.")

if __name__ == "__main__":
    main()
