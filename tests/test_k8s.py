import os
import sys

def validate_k8s_manifests():
    print("Validating Kubernetes Manifests...")
    # Go up one level from 'tests/' to find 'k8s/'
    k8s_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'k8s')
    
    if not os.path.exists(k8s_dir):
        print(f"[FAIL] Directory not found: {k8s_dir}")
        sys.exit(1)
        
    files = [f for f in os.listdir(k8s_dir) if f.endswith('.yaml') or f.endswith('.yml')]
    
    if not files:
        print("[FAIL] No YAML files found in k8s/ directory")
        sys.exit(1)
        
    error_count = 0
    
    for file in files:
        file_path = os.path.join(k8s_dir, file)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Basic structural checks (heuristic to avoid PyYAML dependency requirement)
            if "apiVersion:" not in content:
                print(f"[FAIL] {file}: Missing 'apiVersion'")
                error_count += 1
                continue
                
            if "kind:" not in content:
                print(f"[FAIL] {file}: Missing 'kind'")
                error_count += 1
                continue
                
            if "metadata:" not in content:
                print(f"[FAIL] {file}: Missing 'metadata'")
                error_count += 1
                continue

            # Check for common resource types we expect
            resources = []
            for line in content.splitlines():
                if line.strip().startswith("kind:"):
                    resources.append(line.split(":")[1].strip())
            
            print(f"[PASS] {file}: Valid structure. Found resources: {', '.join(resources)}")
            
        except Exception as e:
            print(f"[FAIL] {file}: Error reading file - {e}")
            error_count += 1
            
    if error_count > 0:
        print(f"\n[FAIL] {error_count} manifest checks failed.")
        sys.exit(1)
    else:
        print("\n[PASS] All Kubernetes manifests passed basic validation.")

if __name__ == "__main__":
    validate_k8s_manifests()
