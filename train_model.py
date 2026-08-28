import os
import time
import copy
import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, transforms, models

# --------------------------------------------------
# 1. SETUP & CONFIGURATION
# --------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(BASE_DIR, "DATASET")
MODELS_DIR = os.path.join(BASE_DIR, "MODELS")
os.makedirs(MODELS_DIR, exist_ok=True)

BATCH_SIZE = 16
NUM_EPOCHS = 15
LEARNING_RATE = 0.001
NUM_CLASSES = 5  # Updated to 5 classes to include Class_0_Not_Drain

# Use GPU if available
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
print(f"🚀 Using computation device: {device}")

# --------------------------------------------------
# 2. DATA AUGMENTATION & TRANSFORMATIONS
# --------------------------------------------------
data_transforms = {
    'train': transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(15),
        transforms.ColorJitter(brightness=0.2, contrast=0.2),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ]),
    'val': transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ]),
}

# --------------------------------------------------
# 3. LOAD DATASETS
# --------------------------------------------------
image_datasets = {
    x: datasets.ImageFolder(os.path.join(DATASET_DIR, x), data_transforms[x])
    for x in ['train', 'val']
}

dataloaders = {
    x: torch.utils.data.DataLoader(image_datasets[x], batch_size=BATCH_SIZE, shuffle=True, num_workers=0)
    for x in ['train', 'val']
}

dataset_sizes = {x: len(image_datasets[x]) for x in ['train', 'val']}
class_names = image_datasets['train'].classes

print(f"📊 Training samples: {dataset_sizes['train']} | Validation samples: {dataset_sizes['val']}")
print(f"🏷️ Classes detected ({len(class_names)}): {class_names}")

# --------------------------------------------------
# 4. INITIALIZE MOBILENETV3 MODEL
# --------------------------------------------------
model = models.mobilenet_v3_small(weights=models.MobileNet_V3_Small_Weights.DEFAULT)

# Replace final classifier layer for 5 classes
num_features = model.classifier[3].in_features
model.classifier[3] = nn.Linear(num_features, NUM_CLASSES)

model = model.to(device)

criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)

# --------------------------------------------------
# 5. TRAINING LOOP
# --------------------------------------------------
def train_drain_model(model, criterion, optimizer, num_epochs=15):
    since = time.time()
    best_model_wts = copy.deepcopy(model.state_dict())
    best_acc = 0.0

    for epoch in range(num_epochs):
        print(f"\nEpoch {epoch + 1}/{num_epochs}")
        print("-" * 30)

        for phase in ['train', 'val']:
            if phase == 'train':
                model.train()
            else:
                model.eval()

            running_loss = 0.0
            running_corrects = 0

            for inputs, labels in dataloaders[phase]:
                inputs = inputs.to(device)
                labels = labels.to(device)

                optimizer.zero_grad()

                with torch.set_grad_enabled(phase == 'train'):
                    outputs = model(inputs)
                    _, preds = torch.max(outputs, 1)
                    loss = criterion(outputs, labels)

                    if phase == 'train':
                        loss.backward()
                        optimizer.step()

                running_loss += loss.item() * inputs.size(0)
                running_corrects += torch.sum(preds == labels.data)

            epoch_loss = running_loss / dataset_sizes[phase]
            epoch_acc = running_corrects.double() / dataset_sizes[phase]

            print(f"{phase.capitalize()} Loss: {epoch_loss:.4f} | Acc: {epoch_acc*100:.2f}%")

            if phase == 'val' and epoch_acc > best_acc:
                best_acc = epoch_acc
                best_model_wts = copy.deepcopy(model.state_dict())

    time_elapsed = time.time() - since
    print(f"\n🎉 Training complete in {time_elapsed // 60:.0f}m {time_elapsed % 60:.0f}s")
    print(f"🏆 Best Validation Accuracy: {best_acc*100:.2f}%")

    model.load_state_dict(best_model_wts)
    return model

# Run training
trained_model = train_drain_model(model, criterion, optimizer, num_epochs=NUM_EPOCHS)

# --------------------------------------------------
# 6. SAVE TRAINED WEIGHTS
# --------------------------------------------------
save_path = os.path.join(MODELS_DIR, "drain_classifier.pth")
torch.save(trained_model.state_dict(), save_path)
print(f"💾 Model weights saved to: {save_path}")