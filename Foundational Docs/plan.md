
### Part 2: Desktop Implementation Plan (Revised for AmbiNeuro)

**2.1 Strategic Overview**
The objective is to implement a macOS desktop application, AmbiNeuro, that serves as a comparative evaluation platform for Ambisonic playback. The application must support arbitrary order input (up to 10th order) , real-time head tracking (Yaw/Pitch/Roll) via OSC , and a modern drag-and-drop interface.

Crucially, it will utilize a dual-engine processing backend. Users will be able to hot-swap between the A2B neural rendering engine  and traditional linear binaural decoders (MagLS, Time-Alignment, Least-Squares, Spatial Re-Sampling) provided by the Spatial Audio Framework (SAF). To achieve low-latency performance suitable for head-tracked binaural audio (motion-to-photon latency < 20ms) , the system will rely on a multi-process architecture utilizing PyTorch with Metal Performance Shaders (MPS) for neural paths  and optimized C/C++ routines via `safpy` for linear paths.

**2.2 System Architecture**
The application drops PySide6 in favor of a Multi-Process Architecture decoupled via WebSockets or ZeroMQ, ensuring the heavy DSP calculations never block the user interface.

**2.2.1 Component Diagram**

1. **Frontend (Electron Renderer - React/TypeScript):** Manages the view layer, processes native OS drag-and-drop events, visualizes head orientation, and provides the control panel for hot-swapping decoder methods and custom HRTFs.
2. **Bridge (Electron Main - Node.js):** Manages the application lifecycle, handles macOS file system and hardware entitlements, and spawns/terminates the Python backend daemon.
3. **Backend Daemon (Python - Headless):**
* **State/Comms Server:** A lightweight WebSocket server listening for UI state changes (e.g., "Switch to MagLS", "Load this .sofa file").
* 
**OSC Receiver Thread:** Listens for UDP packets containing head tracking coordinates. Updates a thread-safe atomic state.


* 
**Audio/Compute Thread (High Priority):** Reads audio frames , adapts the channel count , applies Wigner-D rotation matrices based on the tracker state , routes the signal to the active decoder (A2B or SAF), and pushes stereo samples to the CoreAudio hardware buffer.





**2.2.2 Technology Stack**

* **Frontend:** React, TypeScript, Tailwind CSS (via Vite).
* **Bridge:** Electron.
* 
**Backend Runtime:** Python 3.10+ (Required for stable `torch.backends.mps`).


* 
**Neural Compute Backend:** PyTorch (MPS). Essential for low-latency inference on Mac.


* **Linear Compute Backend:** `safpy` (Python wrappers for the Spatial Audio Framework).
* 
**Audio I/O:** `sounddevice` (PortAudio wrapper).


* 
**Networking:** `python-osc` for tracking, WebSockets for IPC.



**2.3 The Processing Engines & Routing**
Because Ambisonics (represented as Spherical Harmonics) are rotation-invariant, we simulate head movement by rotating the sound field prior to decoding.

* **The Math Engine:** We will implement Wigner-D matrix generation recursively. For the neural path, this occurs on the MPS device via PyTorch to keep the signal path within GPU memory. For the linear path, SAF handles the rotation mathematically on the CPU.


* **The Neural Path (A2B):** Leverages the loaded A2B checkpoint. It handles arbitrary file orders by zero-padding (up-sampling) or truncating (down-sampling)  channels to match the model's expected shape.


* **The Linear Path (SAF):** Routes the rotated signal through the `safpy` binaural decoder. This module must dynamically reload the HRTF mapping whenever the user supplies a custom `.sofa` file via the frontend.

**2.4 macOS Implementation Specifics**

* 
**The Drag-and-Drop Advantage:** Electron's Chromium runtime natively handles local file drops, bypassing the PySide6/macOS `file:///` reference issues. The React app will extract the absolute POSIX path and send it over IPC.


* 
**Audio Permissions:** CoreAudio requires explicit permission. `electron-builder` configuration must inject the `NSMicrophoneUsageDescription` entitlement into the generated `.app` bundle.


* 
**Coordinate Mapping:** The OSC thread must normalize incoming aviation angles (Yaw/Pitch/Roll) to Radians for rotation around the Z, Y, and X axes respectively to match the Ambisonic ACN/SN3D format.



---

### Part 3: Product Requirements Prompt (PRP) for AI Agent

**Agent Persona:** You are an autonomous Senior Software Engineer specializing in Electron, React/TypeScript, Python, and Audio DSP.
**Environment:** Antigravity IDE (VS Code fork).
**Methodology:** Strict Test-Driven Development (TDD). You do not write implementation code until a test has failed.
**Goal:** Build "AmbiNeuro", a multi-process macOS desktop application for neural and linear Ambisonic rendering.

**Phase 1: Multi-Process Environment & Core Architecture**

* **Goal:** Establish the Electron-React frontend and the Python headless backend, bridging them via WebSockets.
* **Prompt:** "Scaffold an `electron-vite` project using React, TypeScript, and Tailwind. Create a separate `backend` directory with a Python virtual environment. The `requirements.txt` must include: `torch`, `sounddevice`, `soundfile`, `numpy`, `python-osc`, `safpy`, and `websockets`. Implement an IPC bridge where the Electron Main process spawns `engine.py` as a child process and the React frontend connects to it via a local WebSocket."
* 
**Test 1.1 (Environment):** Write a Python test that asserts `torch.backends.mps.is_available()` is True. Write a test asserting `safpy` imports without missing C-library dependencies.


* **Test 1.2 (IPC Lifecycle):** Write a script asserting that when Electron quits, the Python child process terminates gracefully. Write a WebSocket ping/pong test between React and Python.

**Phase 2: Audio Loading & Hardware I/O**

* **Goal:** Implement the high-priority audio callback and file loading.
* **Prompt:** "Implement a `.wav` file loader and a multi-threaded ring buffer in Python to decouple the hardware audio callback from the compute blocks."
* 
**Test 2.1 (Ring Buffer):** Initialize a ring buffer of size 4096. Write 2048 samples, read 1024, and assert the read pointer advanced correctly.


* 
**Test 2.2 (Callback):** Mock `sounddevice.OutputStream`. Assert that the callback consumes data from the ring buffer without under-runs.



**Phase 3: Dual Processing Pipeline & Rotation**

* 
**Goal:** Implement real-time Spherical Harmonic rotation  and build the routing matrix for the A2B model and SAF decoders.


* **Prompt:** "In `engine.py`, build a `DecoderGraph`. It must accept Yaw/Pitch/Roll angles and generate Wigner-D matrices for rotation. Implement an `adapt_input` function for channel padding/truncation. Implement routing logic: based on the current state variable, pass the rotated tensor to a mock PyTorch model OR to the `safpy` binaural decoder (supporting MagLS, TA, LS, and SPR methods)."
* **Test 3.1 (Adaptation):** Test `adapt_input(tensor, target_order)`. Case A: Input 4 channels, target 25. Assert output is 25 channels (zero-padded). Case B: Input 49 channels, target 25. Assert output is 25 channels (truncated).


* **Test 3.2 (Dual Routing):** Pass a 1024-sample block with state = 'NEURAL'; assert output is shape (Batch, 2, 1024) via PyTorch. Pass the same block with state = 'LINEAR' and method = 'MagLS'; assert `safpy` returns the correctly shaped stereo array.
* **Test 3.3 (Latency):** Measure execution time of the full path (Rotation + Inference/SAF) on MPS. Assert execution time < 10ms for a 20ms buffer.



**Phase 4: Head Tracking & State Control**

* **Goal:** Enable remote OSC control and handle UI state changes.
* **Prompt:** "Implement an `OSCController` class in Python listening for UDP packets on port 9000. Normalize incoming degrees to radians. Implement a WebSocket listener in `engine.py` that updates the active decoder method and loads `.sofa` files into `safpy` when paths are received."
* 
**Test 4.1 (OSC Mapping):** Input Yaw=90, Pitch=0, Roll=0. Assert the controller outputs the correct Euler angles in Radians (e.g., [1.57, 0, 0]).


* 
**Test 4.2 (Concurrency):** Simulate the OSC thread writing angles while the Audio thread reads them. Assert no race conditions.



**Phase 5: Frontend UI & Visualization**

* **Goal:** Build the React/Tailwind interface.
* **Prompt:** "In the React frontend, build a Tailwind-styled UI. Include a drag-and-drop zone for `.wav` Ambisonic files, a separate drop zone for custom `.sofa` HRTF files, a dropdown to select the active decoder (A2B, MagLS, TA, LS, SPR), and a visual compass mapping the head orientation."
* **Test 5.1 (UI Drag & Drop):** In Vitest, simulate a file drop event. Assert the absolute file path is extracted and sent via the WebSocket payload.
* **Test 5.2 (State Control):** Simulate selecting 'SAF-MagLS' from the dropdown. Assert the correct JSON payload `{"decoder": "SAF-MagLS"}` is emitted over the WebSocket.

**Phase 6: Packaging & Deployment**

* 
**Goal:** Create a distributable macOS `.app` bundle.


* 
**Prompt:** "Configure `electron-builder` and `pyinstaller`. Compile the Python daemon (including `libtorch`, `sounddevice`, and `safpy` binaries) into a standalone executable. Configure Electron to bundle this executable. Add `NSMicrophoneUsageDescription` to the macOS entitlements file."


* **Test 6.1 (Build):** Run the build script and verify the `dist/AmbiNeuro.app` bundle successfully opens and spawns both processes.

