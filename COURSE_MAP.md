# Course Map

Jetson Orin Nano Super 8 GB (JetPack 6.2). Three students share one Jetson. All labs are Jupyter notebooks with step-by-step tasks and check tasks.

The course has four formal parts. Each part also has a short name that says what the student does.

| Part | Formal name | By action | Labs | Status |
|---|---|---|---|---|
| 1 | Foundations | **Get Ready** | 0 to 5 | Built |
| 2 | Applied AI | **Use AI** | 6 to 26 | Built |
| 3 | Fine-Tuning AI | **Adapt AI** | 27 to 29 | Proposed |
| 4 | Machine Learning Fundamentals | **Build AI** | 30 to 35 | Proposed |

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

## Part 2: Applied AI (Use AI), Labs 6 to 26

### Branch 1: Vision AI (Labs 6 to 15)
| Lab | Name |
|---|---|
| 6 | Image Processing with OpenCV (images as numbers, before any AI) |
| 7 | AI Vision and Inference |
| 8 | Optimisation with TensorRT |
| 9 | Mini Project: Object Counter with Alerts |
| 10 | People Tracking and In/Out Counting |
| 11 | Pose Estimation: Exercise Counter |
| 12 | Segmentation and Zones: Free-or-Taken Checker |
| 13 | Read Text (OCR) and QR Codes |
| 14 | Teach the Jetson New Objects (light fine-tuning) |
| 15 | Deploy Your Model: Missing-Item Alarm |

### Branch 2: Speech AI (Labs 16 to 18)
| Lab | Name |
|---|---|
| 16 | Speech to Text |
| 17 | Keyword Spotting: Your Own Wake Word (light training) |
| 18 | Text to Speech |

### Branch 3: Language AI (Labs 19 to 22)
| Lab | Name |
|---|---|
| 19 | Large Language Models (LLM) on Jetson |
| 20 | RAG on Jetson (Retrieval-Augmented Generation) |
| 21 | Vision-Language Model (VLM) on Jetson |
| 22 | Multi-Modal AI Assistant on Jetson |

### Integration (Labs 23 to 26)
| Lab | Name |
|---|---|
| 23 | AIoT: the Jetson Brain and the ESP32-S3 Body |
| 24 | The Smart Door |
| 25 | Sensor Streams, Anomaly Detection and a Live Dashboard |
| 26 | Capstone: Your Own AIoT Application |

Labs 14 and 17 are light training inside Part 2. Each should say: "You used training here. In Part 3 and Part 4 you learn how it works."

## Part 3: Fine-Tuning AI (Adapt AI), Labs 27 to 29 (proposed)

The same three branches as Part 2, so students repeat the pattern they know.

| Lab | Branch | Idea | Open question |
|---|---|---|---|
| 27 | Vision | Fine-tune YOLO properly: dataset quality, augmentation, metrics, overfitting | Overlaps with Lab 14 |
| 28 | Speech | Fine-tune a small speech model on your own voice or accent | Not tested on 8 GB |
| 29 | Language | LoRA fine-tune a tiny LLM on your own Q&A | May not fit in 8 GB shared memory; test first |

## Part 4: Machine Learning Fundamentals (Build AI), Labs 30 to 35 (proposed)

| Lab | Idea |
|---|---|
| 30 | Data and features: tables, train/validation/test split |
| 31 | Classic ML: linear regression, decision trees |
| 32 | A neural network from scratch in PyTorch: loss, backpropagation |
| 33 | A CNN for images: build one and compare it with YOLO |
| 34 | Overfitting, tuning and evaluation |
| 35 | Machine Learning capstone |

Each Part 4 lab opens with: "In Part 2 you used X. Now you build X."

## Decisions still open
1. Keep Labs 14 and 17 in Part 2 as light training, or move them to Part 3 (needs renumbering).
2. Whether Lab 29 (LLM fine-tuning) fits in 8 GB; if not, swap it for fine-tuning a small classifier.
3. Lab numbers in Parts 3 and 4 are placeholders.
4. Not yet tested on hardware: camera, microphone, speaker, ESP32-S3.
