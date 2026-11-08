# Course Map

Jetson Orin Nano Super 8 GB (JetPack 6.2). Three students share one Jetson. All labs are Jupyter notebooks with step-by-step tasks and check tasks.

The course has four formal parts. Each part also has a short name that says what the student does.

| Part | Formal name | By action | Labs | Status |
|---|---|---|---|---|
| 1 | Foundations | **Get Ready** | 0 to 5 | Built |
| 2 | Applied AI | **Use AI** | 6 to 28 | Built, being reorganised (see notes) |
| 3 | Fine-Tuning AI | **Adapt AI** | 29 to 31 | Proposed |
| 4 | Machine Learning Fundamentals | **Build AI** | 32 to 37 | Proposed |

## Part 1: Foundations (Get Ready), Labs 0 to 5

### Jetson and Linux (Labs 0 to 3)
| Lab | Name |
|---|---|
| 0 | See It First: AI Vision Demo |
| 1 | Introduction to Jetson Orin Nano Super |
| 2 | Ubuntu Linux Essentials (Part 1) |
| 3 | Ubuntu Linux Essentials (Part 2) |

### Programming and GPU (Labs 4 to 5)
| Lab | Name |
|---|---|
| 4 | Python on Jetson |
| 5 | NVIDIA CUDA with Python |

## Part 2: Applied AI (Use AI), Labs 6 to 28

No lab in this part trains a model. Students use pretrained models only.

### Branch 1: Vision AI (Labs 6 to 15), following the Ultralytics YOLO tasks
| Lab | Name | Notes |
|---|---|---|
| 6 | Image Processing with OpenCV | Images as numbers, before any AI |
| 7 | YOLO on Jetson and TensorRT Optimisation | First YOLO run, then export to TensorRT so every later lab runs fast |
| 8 | Image Classification | What is in the picture? |
| 9 | Object Detection | What and where? |
| 10 | Oriented Detection (OBB) | Rotated objects (new lab) |
| 11 | Segmentation and Zones | Which exact pixels? |
| 12 | Pose Estimation | Body joints |
| 13 | Object Tracking and Counting | Tracking mode, on top of any task above |
| 14 | Read Text (OCR) and QR Codes | Not YOLO; a "reading" lab |
| 15 | Vision Project: Counter and Missing-Item Alarm | Pretrained models only |

### Branch 2: Speech AI (Labs 16 to 18)
| Lab | Name | Notes |
|---|---|---|
| 16 | Speech to Text | Speech recognition |
| 17 | Keyword Spotting | Pretrained model (own wake word moves to Part 3) |
| 18 | Text to Speech | Piper voice |

### Branch 3: Language AI (Labs 19 to 24)
| Lab | Name | Notes |
|---|---|---|
| 19 | Large Language Models (LLM) | Run llama.cpp yourself, chat, text only |
| 20 | RAG (Retrieval-Augmented Generation) | Answers from your notes |
| 21 | Vision-Language Model (VLM) | Adds eyes (mmproj) to the LLM |
| 22 | Multi-Modal AI Assistant | Vision, speech and language together |
| 23 | Tool Calling | The LLM asks your code to run a function (new lab) |
| 24 | Agentic AI | Agent loop: pick a tool, see the result, decide the next step (new lab) |

The models come first (LLM, RAG, VLM, Multi-Modal). Tool Calling and Agentic AI come after them and lead into the AIoT labs, where the tools become real (sensors, door).

### Integration (Labs 25 to 28)
| Lab | Name |
|---|---|
| 25 | AIoT: the Jetson Brain and the ESP32-S3 Body |
| 26 | The Smart Door |
| 27 | Sensor Streams, Anomaly Detection and a Live Dashboard |
| 28 | Capstone: Your Own AIoT Application |

## Part 3: Fine-Tuning AI (Adapt AI), Labs 29 to 31 (proposed)

The same three branches as Part 2, so students repeat the pattern they know.

| Lab | Branch | Idea | Open question |
|---|---|---|---|
| 29 | Vision | Collect, label and train YOLO on your own images (the old Lab 14) | Needs the old Lab 14 moved here |
| 30 | Speech | Train your own wake word (from the old Lab 17) | Pretrained version stays in Lab 17 |
| 31 | Language | LoRA fine-tune a tiny LLM on your own Q&A | May not fit in 8 GB shared memory; test first |

## Part 4: Machine Learning Fundamentals (Build AI), Labs 32 to 37 (proposed)

| Lab | Idea |
|---|---|
| 32 | Data and features: tables, train/validation/test split |
| 33 | Classic ML: linear regression, decision trees |
| 34 | A neural network from scratch in PyTorch: loss, backpropagation |
| 35 | A CNN for images: build one and compare it with YOLO |
| 36 | Overfitting, tuning and evaluation |
| 37 | Machine Learning capstone |

Each Part 4 lab opens with: "In Part 2 you used X. Now you build X."

## Work needed to match this map
1. Vision: split the old Lab 7 (classify and detect) into Labs 8 and 9; move TensorRT to Lab 7; add OBB (Lab 10, new); reorder segmentation, pose and tracking; merge the old Labs 9 and 15 into the project.
2. Move the old Lab 14 (custom model) to Lab 29, and the training part of Lab 17 to Lab 30.
3. Language: rename Labs 19 to 22 without "on Jetson" (notebooks, teacher app list, README); write Labs 23 and 24.
4. Renumber Integration from Labs 23 to 26 to Labs 25 to 28, and update references (notebooks, teacher app, README, labs-setup.sh).
5. Test Qwen3.5-2B tool calling on the Jetson before writing Labs 23 and 24.

## Decisions still open
1. Whether an LLM fine-tune (Lab 31) fits in 8 GB; if not, swap it for fine-tuning a small classifier.
2. Lab numbers in Parts 3 and 4 are placeholders.
3. Not yet tested on hardware: camera, microphone, speaker, ESP32-S3.
