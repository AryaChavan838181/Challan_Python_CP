import os
import sys
from ultralytics import YOLO
import torch
import platform
import importlib
import shutil
from pathlib import Path

def check_hardware_acceleration():
    """Check for available hardware acceleration options"""
    acceleration = {
        "cuda": torch.cuda.is_available(),
        "cuda_devices": torch.cuda.device_count() if torch.cuda.is_available() else 0,
        "mps": hasattr(torch.backends, "mps") and torch.backends.mps.is_available(),
        "npu": False,
        "device": "cpu"
    }
    
    # Skip Intel NPU/XPU acceleration check on Windows - it causes issues
    if platform.system() != "Windows":
        try:
            # Only attempt to import Intel extensions on Linux/Mac
            import importlib.util
            if importlib.util.find_spec("intel_extension_for_pytorch") is not None:
                acceleration["npu"] = True
        except Exception as e:
            print(f"Note: Intel extensions not loaded: {e.__class__.__name__}")
    
    # Determine best device
    if acceleration["cuda"]:
        acceleration["device"] = "cuda"
        print(f"🚀 CUDA enabled: {acceleration['cuda_devices']} GPU(s) available")
        for i in range(acceleration["cuda_devices"]):
            props = torch.cuda.get_device_properties(i)
            print(f"   GPU {i}: {props.name} ({props.total_memory / 1024**3:.1f} GB)")
    elif acceleration["mps"]:
        acceleration["device"] = "mps"
        print("🚀 Apple Metal Performance Shaders (MPS) enabled")
    elif acceleration["npu"]:
        acceleration["device"] = "xpu" if hasattr(torch, "xpu") else "cpu"
        print("🚀 Intel NPU/XPU acceleration available")
    else:
        print("⚠️ No hardware acceleration available - using CPU (slower)")
    
    print(f"Selected device: {acceleration['device']}")
    return acceleration

def train_yolov11(data_yaml_path, epochs=5, batch_size=16, image_size=320):
    """
    Train YOLOv11 model on license plate dataset - Optimized for SPEED
    
    Args:
        data_yaml_path: Path to data.yaml file that defines dataset locations
        epochs: Number of training epochs (reduced drastically for speed)
        batch_size: Batch size
        image_size: Input image size for training (reduced for speed)
    """
    print("="*80)
    print(f"RAPID TRAINING MODE: YOLOv11 model for license plate detection")
    print(f"Dataset: {data_yaml_path}")
    print(f"Epochs: {epochs}, Batch size: {batch_size}, Image size: {image_size}")
    print("="*80)
    
    # Check for hardware acceleration - safely with error handling
    try:
        accel = check_hardware_acceleration()
        device = accel["device"]
    except Exception as e:
        print(f"Error checking hardware: {e}")
        print("Defaulting to CPU")
        device = "cpu"
    
    # Create models directory
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)
    
    # Pre-cleanup to ensure we have enough disk space
    cache_dirs = [Path(".cache"), Path("runs/detect")]
    for cache_dir in cache_dirs:
        if cache_dir.exists() and cache_dir.is_dir():
            try:
                shutil.rmtree(cache_dir)
                print(f"Cleaned up {cache_dir} for better performance")
            except:
                pass
    
    # Use existing YOLOv11 model - use nano or small model for speed
    try:
        # Try to use the smallest/fastest model available
        print("Loading smallest available YOLO model for rapid training...")
        try:
            model = YOLO("yolov11n.pt")  # Nano model (fastest)
            print("✅ Using YOLOv11n model")
        except:
            try:
                model = YOLO("yolov8n.pt")  # YOLOv8 nano model
                print("✅ Using YOLOv8n model")
            except:
                model = YOLO("yolov8n.pt", task='detect')
                print("✅ Using YOLOv8n model with explicit detect task")
    except Exception as e:
        print(f"❌ Error loading YOLO model: {e}")
        return None
    
    # Optimize training parameters for MAXIMUM SPEED
    training_params = {
        "data": data_yaml_path,
        "epochs": epochs,         # Reduced epochs (5 instead of 100)
        "imgsz": image_size,      # Smaller image size (320 instead of 640)
        "batch": batch_size,
        "device": device,
        "patience": 3,            # Aggressive early stopping
        "project": "models",
        "name": "license_plate_rapid",
        "exist_ok": True,
        "pretrained": True,
        "verbose": True,
        "mosaic": 0,              # Disable mosaic augmentation for speed
        "rect": True,             # Use rectangular training for speed
        "amp": True,              # Always use mixed precision for speed
        "close_mosaic": 0,        # No need to close mosaic if disabled
    }
    
    # Performance optimizations for MAXIMUM SPEED
    if device == "cuda":
        # Maximize GPU utilization
        training_params.update({
            "workers": min(8, os.cpu_count() or 4),  # More workers
            "optimizer": "SGD",   # SGD can be faster than AdamW
            "nbs": 64,            # Nominal batch size
            "single_cls": True,   # Treat as single class problem
            "overlap_mask": False,# No mask overlap (faster)
            "val": False,         # Skip validation during training (saves time)
        })
    else:
        # CPU optimizations for speed
        training_params.update({
            "workers": 0,          # No workers on CPU (less overhead)
            "batch": min(4, batch_size),  # Smaller batch for CPU
            "cache": False,        # No caching
        })
    
    # SPEED HACK: Create a tiny validation subset to save time
    try:
        val_dir = os.path.join(os.path.dirname(data_yaml_path), "val_tiny")
        if not os.path.exists(val_dir):
            os.makedirs(os.path.join(val_dir, "images"), exist_ok=True)
            os.makedirs(os.path.join(val_dir, "labels"), exist_ok=True)
            
            # Copy just a few validation images/labels for faster validation
            import random
            import glob
            import shutil
            
            # Get original val path
            orig_val_dir = os.path.join(os.path.dirname(data_yaml_path), "val")
            orig_val_images = glob.glob(os.path.join(orig_val_dir, "images", "*.*"))
            
            # Select just 5 random images for quick validation
            sample_images = random.sample(orig_val_images, min(5, len(orig_val_images)))
            
            # Copy the selected images and their labels
            for img_path in sample_images:
                img_filename = os.path.basename(img_path)
                label_filename = os.path.splitext(img_filename)[0] + ".txt"
                
                # Copy image
                shutil.copy2(
                    img_path,
                    os.path.join(val_dir, "images", img_filename)
                )
                
                # Try to copy label if it exists
                label_path = os.path.join(orig_val_dir, "labels", label_filename)
                if os.path.exists(label_path):
                    shutil.copy2(
                        label_path,
                        os.path.join(val_dir, "labels", label_filename)
                    )
            
            # Update data.yaml to use tiny validation set
            with open(data_yaml_path, 'r') as f:
                yaml_content = f.read()
            
            yaml_content = yaml_content.replace(f"{orig_val_dir}/images", f"{val_dir}/images")
            
            with open(data_yaml_path, 'w') as f:
                f.write(yaml_content)
                
            print("🚀 Created tiny validation subset for faster training")
    except Exception as e:
        print(f"Warning: Could not optimize validation set: {e}")
    
    print("\n⚡ STARTING RAPID TRAINING WITH PARAMETERS:")
    for key, value in training_params.items():
        print(f"  {key}: {value}")
    
    # Train the model - with accelerated settings
    try:
        print("\n" + "="*50)
        print("🔥 RAPID TRAINING IN PROGRESS - TARGETING <20 MINUTES")
        print("="*50)
        
        # Train with speed-optimized parameters
        results = model.train(**training_params)
        
        # Save the trained model in a lightweight format
        model_save_path = models_dir / "license_plate_rapid.pt"
        model.save(model_save_path)
        print(f"✅ Model saved to {model_save_path}")
    except Exception as e:
        print(f"❌ Error during training: {e}")
        return None
    
    print("🎉 Rapid training complete!")
    return str(model_save_path)

def prepare_dataset(dataset_dir):
    """
    Prepare dataset directory structure and create data.yaml
    
    Args:
        dataset_dir: Path to directory containing the dataset
    
    Returns:
        Path to data.yaml file
    """
    # Create necessary directories
    train_dir = os.path.join(dataset_dir, "train")
    val_dir = os.path.join(dataset_dir, "val")
    
    # Check if directories exist
    if not os.path.exists(train_dir) or not os.path.exists(val_dir):
        print(f"Error: Training or validation directory not found in {dataset_dir}")
        print("Please structure your dataset as follows:")
        print(f"  {dataset_dir}/")
        print(f"  ├── train/")
        print(f"  │   ├── images/")
        print(f"  │   └── labels/")
        print(f"  └── val/")
        print(f"      ├── images/")
        print(f"      └── labels/")
        return None
    
    # Create data.yaml file
    data_yaml_path = os.path.join(dataset_dir, "data.yaml")
    with open(data_yaml_path, "w") as f:
        f.write(f"train: {train_dir}/images\n")
        f.write(f"val: {val_dir}/images\n")
        f.write("nc: 1\n")  # Number of classes (1 for license plate)
        f.write("names: ['license_plate']\n")
    
    print(f"Created data.yaml at {data_yaml_path}")
    return data_yaml_path

if __name__ == "__main__":
    print("╔═════════════════════════════════════════════════╗")
    print("║     RAPID License Plate Detector Training       ║")
    print("║       (Optimized for under 20 minutes)          ║")
    print("╚═════════════════════════════════════════════════╝")
    
    # Check if ultralytics is installed and up to date
    try:
        import importlib.metadata
        ultralytics_version = importlib.metadata.version('ultralytics')
        print(f"Using ultralytics version: {ultralytics_version}")
        
        # Make sure YOLO model is accessible - try v11 first, then v8
        print("Verifying YOLO model availability...")
        try:
            model = YOLO("yolov11n.pt")
            model_name = "YOLOv11"
        except:
            try:
                model = YOLO("yolov8n.pt")
                model_name = "YOLOv8"
            except Exception as e:
                print(f"❌ Error loading any YOLO model: {e}")
                print("Please install ultralytics and download a YOLO model")
                sys.exit(1)
        print(f"✅ {model_name} model is ready")
    except Exception as e:
        print(f"❌ Error checking ultralytics: {e}")
        print("\nPlease ensure ultralytics is properly installed:")
        print("pip install -r requirements.txt")
        sys.exit(1)
    
    # Check if dataset directory is provided
    if len(sys.argv) > 1:
        dataset_dir = sys.argv[1]
    else:
        dataset_dir = input("Enter path to dataset directory: ")
    
    # Prepare dataset
    data_yaml_path = prepare_dataset(dataset_dir)
    if data_yaml_path:
        # Train model with MAXIMUM speed optimizations
        train_yolov11(data_yaml_path, epochs=5, batch_size=32, image_size=320)
