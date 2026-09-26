import psutil
import platform
import subprocess
import json
import urllib.request

def inspect_hardware():
    print("=" * 60)
    print("HARDWARE & INFERENCE ENVIRONMENT INSPECTION")
    print("=" * 60)

    # OS & Architecture
    print(f"OS: {platform.platform()}")
    print(f"Machine: {platform.machine()}")
    print(f"Architecture: {platform.architecture()[0]}")

    # CPU
    cpu_name = platform.processor()
    try:
        wmic_cpu = subprocess.check_output(
            ["powershell", "-NoProfile", "-Command", "Get-CimInstance Win32_Processor | Select-Object -ExpandProperty Name"],
            text=True
        ).strip()
        if wmic_cpu:
            cpu_name = wmic_cpu
    except Exception:
        pass
    print(f"CPU Model: {cpu_name}")
    print(f"Physical Cores: {psutil.cpu_count(logical=False)}")
    print(f"Logical Threads: {psutil.cpu_count(logical=True)}")

    # RAM
    mem = psutil.virtual_memory()
    print(f"Total System RAM: {mem.total / (1024**3):.2f} GB")
    print(f"Available System RAM: {mem.available / (1024**3):.2f} GB")
    print(f"Used System RAM: {mem.used / (1024**3):.2f} GB ({mem.percent}%)")

    # GPU
    print("\n--- GPU & Display Adapters ---")
    try:
        smi = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=name,memory.total,memory.free,driver_version", "--format=csv,noheader"],
            text=True
        ).strip()
        print(f"NVIDIA GPU Detected: {smi}")
    except Exception as e:
        print("nvidia-smi not available or no NVIDIA discrete GPU.")

    try:
        gpu_info = subprocess.check_output(
            ["powershell", "-NoProfile", "-Command", "Get-CimInstance Win32_VideoController | Select-Object Name, @{N='VRAM_MB';E={[math]::round($_.AdapterRAM/1MB)}}, DriverVersion | Format-Table -AutoSize | Out-String"],
            text=True
        ).strip()
        print(f"Video Controllers:\n{gpu_info}")
    except Exception as e:
        print(f"Failed to query Win32_VideoController: {e}")

    # Storage
    print("\n--- Storage Devices ---")
    try:
        disk_info = subprocess.check_output(
            ["powershell", "-NoProfile", "-Command", "Get-CimInstance Win32_DiskDrive | Select-Object Model, MediaType, @{N='Size_GB';E={[math]::round($_.Size/1GB, 2)}} | Format-Table -AutoSize | Out-String"],
            text=True
        ).strip()
        print(f"Disk Drives:\n{disk_info}")
    except Exception as e:
        print(f"Disk query error: {e}")

    # Ollama Service & Models
    print("\n--- Ollama Service & Model State ---")
    try:
        req = urllib.request.urlopen("http://localhost:11434/api/tags", timeout=5)
        data = json.loads(req.read().decode())
        models = data.get("models", [])
        print(f"Ollama Service: RUNNING (HTTP 200)")
        print(f"Installed Models ({len(models)}):")
        for m in models:
            size_gb = m.get("size", 0) / (1024**3)
            details = m.get("details", {})
            print(f"  - {m.get('name')}: {size_gb:.2f} GB (family={details.get('family')}, param={details.get('parameter_size')}, quant={details.get('quantization_level')})")
    except Exception as e:
        print(f"Ollama API /tags query error: {e}")

    # Check active running models
    try:
        req = urllib.request.urlopen("http://localhost:11434/api/ps", timeout=5)
        data = json.loads(req.read().decode())
        running_models = data.get("models", [])
        print(f"\nActive In-Memory Ollama Models ({len(running_models)}):")
        for rm in running_models:
            vram_mb = rm.get("size_vram", 0) / (1024**2)
            total_mb = rm.get("size", 0) / (1024**2)
            print(f"  - {rm.get('name')}: total={total_mb:.1f} MB, VRAM={vram_mb:.1f} MB (expires_at={rm.get('expires_at')})")
    except Exception as e:
        print(f"Ollama API /ps query error: {e}")

    print("=" * 60)

if __name__ == "__main__":
    inspect_hardware()
