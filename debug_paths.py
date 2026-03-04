#!/usr/bin/env python3
import os
import sys

print("[v0] Current Working Directory:", os.getcwd())
print("[v0] sys.argv[0]:", sys.argv[0])
print("[v0] Files in current dir:")
for f in os.listdir(os.getcwd()):
    print(f"  - {f}")

print("\n[v0] Checking /vercel/share/v0-project:")
if os.path.exists("/vercel/share/v0-project"):
    print("  EXISTS!")
    print("  Contents:")
    for f in os.listdir("/vercel/share/v0-project"):
        print(f"    - {f}")
else:
    print("  DOES NOT EXIST")

print("\n[v0] Checking parent directories:")
cwd = os.getcwd()
parts = cwd.split("/")
for i in range(1, len(parts)):
    path = "/" + "/".join(parts[1:i+1])
    if os.path.exists(path):
        print(f"  ✓ {path}")
        if i == len(parts) - 1:
            print(f"    Contents: {os.listdir(path)[:5]}")
    else:
        print(f"  ✗ {path}")
