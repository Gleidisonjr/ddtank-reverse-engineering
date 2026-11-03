import os
import shutil

ROOT_DIR = r"C:\Users\dopamine\Desktop\Projetos\Reverse Engineering"
SCRIPTS_DIR = os.path.join(ROOT_DIR, "scripts")
PROBES_DIR = os.path.join(SCRIPTS_DIR, "probes")
LEGACY_DIR = os.path.join(SCRIPTS_DIR, "legacy_launchers")

os.makedirs(PROBES_DIR, exist_ok=True)
os.makedirs(LEGACY_DIR, exist_ok=True)

# 1. Clean root directory
legacy_bats = [
    "launch_4_terminals.bat",
    "launch_game_ultra_hd.bat",
    "launch_offline_emulator.bat",
    "launch_original_game.bat",
    "launch_s2rebirth_direct.bat",
    "launch_s2rebirth_online.bat",
    "launch_workspace_wt.bat",
    "launch_workspace_wt.ps1",
    "open_agy_terminal.bat",
    "iniciar_launcher.bat"
]

for b in legacy_bats:
    p = os.path.join(ROOT_DIR, b)
    if os.path.exists(p):
        dest = os.path.join(LEGACY_DIR, b)
        shutil.move(p, dest)
        print(f"Moved {b} -> scripts/legacy_launchers/")

# Keep essential root files:
# D187_Launcher.bat, launch_game.bat, README.md, AGENTS.md, decisions.md, Home.md, CLAUDE.md

# 2. Clean scripts directory - move probe/test scripts to scripts/probes/
keep_scripts = {
    "d187-mock-server.py",
    "d187_launcher.py",
    "d187_web_portal.py",
    "d187_web_panel.py",
    "d187_protocol.py",
    "d187_match_simulator.py",
    "d187_navmesh_generator.py",
    "d187_profile_service.py",
    "d187_server_runner.py",
    "d187_dedicated_gateway.py",
    "d187_proxy_sniffer.py",
    "inspect_world00p.py",
    "extract_resdt.py",
    "extract_fmod_audio.py",
    "extract_lithtech_cvars.py",
    "build_s2rebirth_dataset.py",
    "s2rebirth_api_client.py",
    "generate_match_heatmap.py",
    "generate_weapon_analytics.py",
    "test_client_handshake_smoke.py",
    "apexguard_stub.py",
    "parse_parquet_binary.py",
    "convert-model00p-to-obj.py"
}

for item in os.listdir(SCRIPTS_DIR):
    item_path = os.path.join(SCRIPTS_DIR, item)
    if os.path.isfile(item_path):
        if item.endswith(".py") and item not in keep_scripts:
            dest = os.path.join(PROBES_DIR, item)
            shutil.move(item_path, dest)
            print(f"Archived probe: {item} -> scripts/probes/")

print("\nCleanup completed successfully!")
