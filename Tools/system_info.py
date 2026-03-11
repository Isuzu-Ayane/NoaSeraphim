import platform
import subprocess
import sys
import psutil
import pkg_resources
import torch

def run(cmd):
    try:
        return subprocess.check_output(cmd, shell=True, text=True).strip()
    except:
        return "N/A"


print("===== AI SYSTEM INFO =====\n")

# -------------------------
# PC
# -------------------------
print("=== SYSTEM ===")

system_manufacturer = run(
'powershell -command "(Get-CimInstance Win32_ComputerSystem).Manufacturer"'
)

system_model = run(
'powershell -command "(Get-CimInstance Win32_ComputerSystem).Model"'
)

bios_serial = run(
'powershell -command "(Get-CimInstance Win32_BIOS).SerialNumber"'
)

bios_version = run(
'powershell -command "(Get-CimInstance Win32_BIOS).SMBIOSBIOSVersion"'
)

print("Manufacturer :", system_manufacturer)
print("Model        :", system_model)
print("Serial       :", bios_serial)
print("BIOS Version :", bios_version)

print()

# -------------------------
# OS
# -------------------------
print("=== OS ===")

import winreg

key = winreg.OpenKey(
    winreg.HKEY_LOCAL_MACHINE,
    r"SOFTWARE\Microsoft\Windows NT\CurrentVersion"
)

product = winreg.QueryValueEx(key, "ProductName")[0]
build = int(winreg.QueryValueEx(key, "CurrentBuildNumber")[0])
ubr = winreg.QueryValueEx(key, "UBR")[0]

try:
    display = winreg.QueryValueEx(key, "DisplayVersion")[0]
except:
    display = "N/A"

# Windows11判定
if build >= 22000:
    product = product.replace("Windows 10", "Windows 11")

print(f"OS           : {product}")
print(f"Version      : {display}")
print(f"Build        : {build}")
print(f"Build Detail : {build}.{ubr}")

print()

# -------------------------
# CPU
# -------------------------
cpu_name = run('powershell -command "(Get-CimInstance Win32_Processor).Name"')
cpu_vendor = run('powershell -command "(Get-CimInstance Win32_Processor).Manufacturer"')
cpu_cores = psutil.cpu_count(logical=False)
cpu_threads = psutil.cpu_count()
cpu_clock = run('powershell -command "(Get-CimInstance Win32_Processor).MaxClockSpeed"')

print("=== CPU ===")
print("Vendor :", cpu_vendor.replace("GenuineIntel","Intel"))
print("Model  :", cpu_name.replace("13th Gen Intel(R) Core(TM) ",""))
print("Cores  :", cpu_cores)
print("Threads:", cpu_threads)
print("Base Clock :", cpu_clock, "MHz")
print()


# -------------------------
# MEMORY
# -------------------------
mem = run(
'powershell -command "Get-CimInstance Win32_PhysicalMemory | Select Manufacturer,PartNumber,Speed,Capacity"'
)
print("=== MEMORY ===")

print("Total RAM:", round(psutil.virtual_memory().total / (1024**3),2), "GB")
print(mem)

print()


# -------------------------
# GPU
# -------------------------

gpu_vendor = run(
'powershell -command "(Get-CimInstance Win32_VideoController).AdapterCompatibility"'
)

gpu_model = run(
'powershell -command "(Get-CimInstance Win32_VideoController).Name"'
)
print("=== GPU ===")

gpu_name = run("nvidia-smi --query-gpu=name --format=csv,noheader")
gpu_mem = run("nvidia-smi --query-gpu=memory.total --format=csv,noheader")
gpu_bus = run("nvidia-smi --query-gpu=pci.bus_id --format=csv,noheader")
vram_mb = int(gpu_mem.split()[0])
vram_gb = round(vram_mb / 1024)
print("Model:", gpu_name)
print()
print("Detected VRAM :", vram_gb, "GB")
print()
print("PCI  :", gpu_bus)
print("Vendor:", gpu_vendor)

# --- VRAM 数値化 ---
try:
    vram_mb = int(gpu_mem.split()[0])
    vram_gb = round(vram_mb / 1024)
except:
    vram_gb = 0

import torch

if torch.cuda.is_available():

    cc = torch.cuda.get_device_capability(0)
    gpu_name = torch.cuda.get_device_name(0)

    compute = f"{cc[0]}.{cc[1]}"

    print("Compute Capability :", compute)

print()


# -------------------------
# STORAGE
# -------------------------
print("=== STORAGE ===")

disks = run("powershell -command \"Get-PhysicalDisk | Select FriendlyName,MediaType,BusType,Size\"")
print(disks)

print("\nMounted volumes:")

for p in psutil.disk_partitions():
    try:
        usage = psutil.disk_usage(p.mountpoint)
        print(f"{p.device} {round(usage.total/1024**3)} GB ({p.fstype})")
    except:
        pass

for part in psutil.disk_partitions():
    try:
        usage = psutil.disk_usage(part.mountpoint)

        total = round(usage.total / (1024**3))
        used = round(usage.used / (1024**3))
        free = round(usage.free / (1024**3))
        percent = usage.percent

        print(f"{part.device}")
        print(f"  Total : {total} GB")
        print(f"  Used  : {used} GB")
        print(f"  Free  : {free} GB")
        print(f"  Usage : {percent}%")
        print()

    except PermissionError:
        pass

print()


# -------------------------
# CUDA
# -------------------------
print("=== CUDA ===")

print("Driver:", run("nvidia-smi --query-gpu=driver_version --format=csv,noheader"))
print("CUDA (driver):", run("nvidia-smi | findstr CUDA"))

if torch:
    print("PyTorch CUDA:", torch.version.cuda)
    print("CUDA Available:", torch.cuda.is_available())
    if torch.cuda.is_available():
        print("GPU Device:", torch.cuda.get_device_name(0))

print()


# -------------------------
# PYTHON
# -------------------------
print("=== PYTHON ===")

print("Current Python:", sys.version)

print("\nInstalled Python versions:")
print(run("py -0"))

print("\nPip packages:")
packages = sorted([p.project_name for p in pkg_resources.working_set])
for p in packages:
    print(p)

print()


# -------------------------
# AI MODULE CHECK
# -------------------------
print("=== AI MODULES ===")

modules = [
    "torch",
    "torchvision",
    "torchaudio",
    "diffusers",
    "transformers",
    "accelerate",
    "safetensors",
    "xformers",
    "bitsandbytes",
    "cv2",
    "numpy",
    "PIL"
]

for m in modules:
    try:
        __import__(m)
        print(m, "OK")
    except:
        print(m, "NOT INSTALLED")




if vram_gb >= 24:
    tier = "High-End AI"
elif vram_gb >= 12:
    tier = "Advanced"
elif vram_gb >= 8:
    tier = "Midrange"
else:
    tier = "Entry"

if vram_gb >= 24:
    img = "◎"
    sdxl = "◎"
    lora = "◎"
    llm7 = "◎"
    llm13 = "◎"

elif vram_gb >= 12:
    img = "◎"
    sdxl = "◎"
    lora = "◎"
    llm7 = "◎"
    llm13 = "○"

elif vram_gb >= 8:
    img = "◎"
    sdxl = "○"
    lora = "○"
    llm7 = "○"
    llm13 = "△"

else:
    img = "○"
    sdxl = "△"
    lora = "△"
    llm7 = "△"
    llm13 = "×"

print("=== AI SPECS ===")
print("あなたのPCでの得意分野は")
print()
print("画像生成 :", img)
print("SDXL :", sdxl)
print("LoRA学習 :", lora)
print("LLM 7B :", llm7)
print("LLM 13B :", llm13)

print()
print("=== VRAM ===")
print("VRAM ≥ 24GB → High-End AI")
print("VRAM ≥ 12GB → Advanced")
print("VRAM ≥ 8GB  → Midrange")
print("VRAM < 8GB  → Entry")

print()
print("あなたのスペックは：「", tier, "」です")
print()


import torch

print("=== AI Environment ===")

print("PyTorch Version :", torch.__version__)

if torch.cuda.is_available():
    print("CUDA Available  : Yes")
    print("CUDA Version    :", torch.version.cuda)
    print("GPU Name        :", torch.cuda.get_device_name(0))
    print("Compute Cap.    :", torch.cuda.get_device_capability(0))
else:
    print("CUDA Available  : No")


import importlib

packages = ["torch","xformers","diffusers","transformers","bitsandbytes"]

for p in packages:
    try:
        importlib.import_module(p)
        print(p,": OK")
    except:
        print(p,": Not Installed")


print("\n===== END =====")

input("\n完了しました。エンターキーを押すと閉じます...")
