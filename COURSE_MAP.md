# Course Map

**Course:** Jetson Orin Nano Super — Applied AI and AIoT  
**Version:** Revised 8 November 2026  
**Learning approach:** Hands-on first → easy to implement → progressive complexity → real-world integration.  
**Structure:** **4 parts · 42 labs (Lab 0–41) · 7 project milestones**.

> **Curriculum principle:** Lab order is based on **practical implementation difficulty**, required prerequisites, integration complexity, and troubleshooting effort—not a universal ranking of the theoretical difficulty of AI disciplines. Each lab should produce a working, demonstrable result. Quality matters more than a fixed lab count.

| Part | Name | Action | Labs | End-of-part outcome |
|---|---|---|---|---|
| 1 | Foundations | Get Ready | 0–5 | Jetson System Monitor |
| 2 | Applied AI | Use AI | 6–31 | Intelligent AIoT System |
| 3 | AI Model Customization | Adapt AI | 32–35 | Custom AI Model Challenge |
| 4 | Machine Learning & Deep Learning Fundamentals | Train AI | 36–41 | Train and Evaluate Your Own AI Model |

## Part 1: Foundations (Get Ready)

**Outcome:** Set up and use the Jetson, work comfortably in Ubuntu Linux, write Python programs, and explore GPU acceleration.

### Jetson and Linux

| Lab | Name | Hands-on outcome |
|---|---|---|
| 0 | Experience AI Vision | Run or observe an instructor-provided AI vision demo; identify its input, inference, and output. |
| 1 | Getting Started with NVIDIA Jetson Orin Nano Super | Identify ports and components, check JetPack and system health, and verify the development environment. |
| 2 | Ubuntu Linux Essentials (Part 1) | Navigate directories, manage files, and use basic terminal commands. |
| 3 | Ubuntu Linux Essentials (Part 2) | Manage packages, processes, permissions, networking, and connected devices. |

### Programming and GPU

| Lab | Name | Hands-on outcome |
|---|---|---|
| 4 | Python Programming on Jetson | Write scripts with variables, functions, packages, file I/O, and error handling. |
| 5 | Introduction to GPU Computing with Python | Compare simple CPU/GPU operations using a supported library; build a basic Jetson System Monitor. |

**Project milestone 1 — Jetson System Monitor (Lab 5):** Display system memory, CPU/GPU activity where supported, temperatures, and a timestamp in a Python dashboard or terminal interface. **No extra lab number.**

> **Scope:** Lab 5 introduces GPU concepts using existing libraries. Writing custom CUDA kernels is not required for beginners.

## Part 2: Applied AI (Use AI)

**Outcome:** Implement pretrained computer vision, speech, and language capabilities before connecting them to external tools and an ESP32-S3 system.

### Vision AI

| Lab | Name | Hands-on outcome |
|---|---|---|
| 6 | Image Processing with OpenCV | Capture and preprocess camera images: resize, crop, color conversion, thresholding, and annotation. |
| 7 | Barcode and QR Code Detection | Decode printed QR codes and supported barcodes using a camera and existing libraries. |
| 8 | Optical Character Recognition (OCR) | Extract text from simple printed labels using a pretrained OCR engine; compare preprocessing results. |
| 9 | Image Classification | Run a pretrained classifier and interpret the top predicted classes and scores. |
| 10 | Object Detection with YOLO | Run a pretrained detector on images/video and visualize bounding boxes and confidence scores. |
| 11 | Oriented Bounding Box (OBB) Detection | Detect objects with rotated bounding boxes using a compatible pretrained OBB model. |
| 12 | Instance Segmentation and Region-of-Interest (ROI) Monitoring | Visualize instance masks and apply spatial zone rules; distinguish segmentation from ROI logic. |
| 13 | Human Pose Estimation | Visualize body keypoints and implement a simple keypoint-based rule. |
| 14 | Object Tracking and Counting | Track detected objects between frames and count line/zone crossings. |
| 15 | AI Inference Optimization with NVIDIA TensorRT | Compare a supported model's baseline and optimized inference with reproducible latency/throughput measurements. |
| 16 | Vision AI Mini-Project: Object Counter and Missing-Item Alert | Combine detection or tracking with counting, presence rules, visual feedback, and alerts. |

**Project milestone 2 — Vision AI (Lab 16):** Demonstrate an **Object Counter and Missing-Item Alert**, with test scenarios and clearly documented detection/alert rules.

> **Scope:** QR/barcode decoding may use classical computer vision rather than machine learning. Introductory OCR is deliberately early because running a pretrained OCR pipeline is often straightforward; difficult OCR cases are advanced. OBB, segmentation, and pose are illustrative branches of vision AI, not strict prerequisites of each other. Confirm model support and licensing before delivery.

### Speech AI

| Lab | Name | Hands-on outcome |
|---|---|---|
| 17 | Automatic Speech Recognition (Speech-to-Text) | Convert supplied audio and microphone speech to text with a pretrained ASR model. |
| 18 | Text-to-Speech (TTS) Synthesis | Generate intelligible speech from text using a supported TTS engine. |
| 19 | Keyword Spotting and Wake-Word Detection | Detect a chosen wake word (or use push-to-talk fallback) and assemble basic voice interaction. |

**Project milestone 3 — Speech AI (Lab 19):** Build a **Voice-Controlled Assistant** that accepts speech, processes simple fixed commands, and replies with synthesized speech. This does not require an LLM or agent.

### Language AI

| Lab | Name | Hands-on outcome |
|---|---|---|
| 20 | Large Language Models (LLMs) and Prompt Engineering | Run or access an LLM; practise system/user instructions, context, few-shot examples, structured JSON output, and simple output checks. |
| 21 | Vision-Language Models (VLMs) | Ask natural-language questions about an image using a compatible VLM. |
| 22 | Audio Language Models: Speech In, Speech Out | Run an audio language model (LFM3-Audio) on the Jetson: turn speech into text, speak text aloud, and compare it with the dedicated speech models of Labs 17 and 18. |
| 23 | Multimodal AI: Text, Vision and Speech | Combine text, images/camera input, speech-to-text, and text-to-speech in a basic multimodal interaction. |
| 24 | Text Embeddings and Retrieval-Augmented Generation (RAG) | Embed short documents, retrieve relevant passages, and generate grounded answers with source references. |
| 25 | LLM Tool Calling and API Integration | Let an LLM request a defined Python tool; validate arguments, call a local/simulated HTTP API, and return tool results to the model. |
| 26 | Model Context Protocol (MCP) | Build a Python MCP **server** exposing tools; connect an MCP **client**, discover and invoke tools, and compare MCP with direct integration. |
| 27 | AI Agents and Workflow Automation | Build a bounded multistep agent; use direct or MCP tools, maintain workflow state, handle failures, and request approval for consequential actions. |

**Project milestone 4 — Language AI (Lab 27):** Build an **AI Agent with Direct Tools and MCP Integration**. Reuse the same simulated sensor tools from Labs 25–26; demonstrate at least one workflow without MCP and one with MCP.

> **Important distinctions:** API integration exchanges data with an external service. LLM tool calling requests a function but application code executes it. MCP standardizes how hosts/clients discover and access tools, resources, and prompts exposed by servers. An agent orchestrates steps toward a goal and **does not require MCP**. A basic multimodal lab does not require an agent.

### AIoT Integration

| Lab | Name | Hands-on outcome |
|---|---|---|
| 28 | AIoT Integration: Jetson as the Brain, ESP32-S3 as the Controller | Exchange real sensor data and commands over a documented transport such as HTTP or MQTT. |
| 29 | Smart Door: AI Vision and IoT Access Control | Connect a vision event to a simulated/low-voltage door-control demonstrator with manual override and safe default state. |
| 30 | Sensor Data Streaming, Anomaly Detection and Real-Time Dashboard | Display live data and implement threshold-based or pretrained anomaly detection; distinguish simple rules from learned anomaly models. |
| 31 | AIoT Capstone: Build Your Own Intelligent System | Build and test a complete Jetson + ESP32-S3 application using relevant AI modalities and a documented workflow. |

**Project milestone 5 — AIoT Integration (Lab 31):** Deliver an **Intelligent AIoT System** with demonstration, clear system diagram, input-to-action flow, and failure/safety checks. Combining several AI domains is encouraged when practical, but not compulsory.

## Part 3: AI Model Customization (Adapt AI)

**Outcome:** Understand the training basics needed for customization, adapt an existing model where applicable, and measure whether the adaptation helped.

| Lab | Name | Hands-on outcome |
|---|---|---|
| 32 | Model Training Essentials: Datasets, Epochs, Loss and Evaluation | Explore labeling, train/validation/test splits, loss curves, epochs, metrics, and overfitting with a tiny guided example. |
| 33 | Fine-Tuning Vision AI: Custom YOLO Object Detector | Label a small image dataset, train or fine-tune a compatible detection model, and evaluate results against a baseline. |
| 34 | Custom Speech AI: Train Your Own Wake-Word Model | Prepare labeled audio clips and train or adapt a compact wake-word/keyword-spotting model. |
| 35 | Fine-Tuning Language AI: LoRA on a Small LLM | Prepare a small instruction dataset and conduct parameter-efficient adaptation on feasible hardware; compare baseline and adapted outputs. |

**Project milestone 6 — AI Model Customization (Lab 35 assessment):** Complete **one** specialization track (vision, speech, or language) and present the dataset, method, trained/adapted model, demonstration, and before/after evaluation. Other customization labs can use guided demonstrations or small-scale exercises.

> **Scope:** Training a wake-word model from scratch is *not* fine-tuning. LoRA does not mean training an LLM from scratch. Large-model training may exceed the Jetson Orin Nano Super's practical memory/compute budget; use small models, careful memory management, or separate GPU resources when necessary. Lab 32 is a practical prerequisite primer, not a replacement for the deeper ML theory in Part 4.

## Part 4: Machine Learning & Deep Learning Fundamentals (Train AI)

**Outcome:** Understand core learning algorithms more deeply and carry out a reproducible train–evaluate–infer workflow.

| Lab | Name | Hands-on outcome |
|---|---|---|
| 36 | Datasets, Features, Labels and Data Preparation | Clean data, define features/labels, prevent data leakage, and create appropriate splits. |
| 37 | Classical Machine Learning: Classification and Regression | Train and compare simple supervised learning models with suitable metrics. |
| 38 | Building a Neural Network from Scratch | Implement a tiny neural network (e.g. in NumPy) to explore forward propagation, loss, gradients, and weight updates. |
| 39 | Convolutional Neural Networks (CNNs) for Image Classification | Train and test a small image CNN using a suitable framework. |
| 40 | Model Evaluation, Overfitting and Hyperparameter Tuning | Compare held-out results, investigate overfitting, and change one hyperparameter at a time. |
| 41 | Machine Learning Capstone: Train and Evaluate Your Own Model | Prepare data, select a baseline, train/evaluate a model, and demonstrate reproducible inference. |

**Project milestone 7 — ML & Deep Learning (Lab 41):** Submit a working model, baseline comparison, evaluation on held-out data, training notes, and an inference demo.

## Seven Project Milestones

| # | Part / domain | Lab | Deliverable |
|---|---|---|---|
| 1 | Foundations | 5 | Jetson System Monitor |
| 2 | Applied AI / Vision | 16 | Object Counter and Missing-Item Alert |
| 3 | Applied AI / Speech | 19 | Voice-Controlled Assistant |
| 4 | Applied AI / Language | 27 | AI Agent with Direct Tools and MCP Integration |
| 5 | Applied AI / AIoT | 31 | Intelligent AIoT System |
| 6 | AI Model Customization | 35 | Custom AI Model Challenge |
| 7 | ML & Deep Learning Fundamentals | 41 | Train and Evaluate Your Own AI Model |

## Lab Development Standards

For **each lab**, provide:

1. **Objective and outcome:** One primary concept and a visible, testable result.
2. **Prerequisites:** Prior labs/skills and any background concepts needed.
3. **Hardware/software:** Devices, interfaces, supported JetPack, Python packages, pinned model versions and licenses.
4. **Setup and hands-on procedure:** Clear steps and working example code.
5. **Validation:** Expected output, repeatable test, and brief explanation of why it works.
6. **Troubleshooting:** Likely problems and fixes, including GPU memory, dependencies, camera/microphone, and networking.
7. **Safety and responsibility:** Permissions, approval gates for actions, privacy considerations, and safe behavior of actuators.
8. **Exercise classification:** Mark clearly as *traditional software/CV*, *pretrained AI inference*, *integration*, *fine-tuning*, or *training from scratch*.

> **Release-readiness note:** This file is a revised **curriculum map**, not proof that each lab's code, exact model, driver, dependency combination, and runtime performance have already been tested on the intended Jetson hardware. Validate those details while authoring the lab manuals.
