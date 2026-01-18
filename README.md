# BlockWar
A UE5 Game: Build Forts, Battle for Victory

## About
BlockWar is an innovative multiplayer FPS that combines tactical base construction with team-based combat. Build elaborate fortifications during the build phase, then battle it out in intense combat to capture the enemy flag.

Built in Unreal Engine 5, inspired by classic community mods.

## Technical Approach

**Procedural Generation + Unit Testing**: BlockWar uses UE5's native procedural generation tools (PCG Framework, Blueprints, C++, Python, Geometry Script) to create game content. This approach enables comprehensive unit testing while maintaining tight engine integration.

**Key Technologies:**
- **UE5 PCG Framework**: Level and content generation
- **Geometry Script**: Procedural mesh generation
- **Python**: Editor automation and unit testing
- **C++**: Performance-critical systems and testing
- **Blueprints**: Gameplay logic and procedural workflows

## Documentation
- [DESIGN_BRIEF.md](DESIGN_BRIEF.md) - Comprehensive game design documentation
- See "Procedural Generation Strategy" section for detailed technical approach and testing methodology
See [DESIGN_BRIEF.md](DESIGN_BRIEF.md) for comprehensive game design documentation.

## GitHub Actions diagnostics
This repository ships with a lightweight "workflow doctor" to help ChatGPT/Codex-style agents quickly understand and triage GitHub Actions issues without running the workflows themselves.

### Setup
1. Install the dependency:
   ```bash
   pip install -r requirements.txt
   ```

### Usage
- Inspect the repository from its root:
  ```bash
  python tools/workflow_doctor.py
  ```

- Only print actionable diagnostics (skip verbose summaries):
  ```bash
  python tools/workflow_doctor.py --quiet
  ```

When no workflow files are present, the tool reports that the `.github/workflows` directory is empty so that agents don't waste time chasing nonexistent CI definitions.
