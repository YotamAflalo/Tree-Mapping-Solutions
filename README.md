# AWS Tree Detection System

An automated system for processing and analyzing aerial/satellite imagery to detect trees using AWS infrastructure. The system processes images daily, splits them into manageable chunks, runs detection models, and aggregates results.

## System Architecture

![System Architecture Diagram]

The system consists of four main components:

1. **Pre-processing Container**
   - Runs daily to process input images
   - Converts TIF images to PNG
   - Splits images into smaller chunks for efficient processing
   - Uploads processed images and offset data to S3
   - Maintains processed files history

2. **Offset Splitter Lambda**
   - Triggers automatically when offset files are uploaded to S3
   - Splits large offset files into smaller chunks
   - Creates individual offset files for parallel processing

3. **Tree Detection Lambda**
   - Custom Docker-based Lambda function
   - Triggered by mini-offset file creation
   - Processes image chunks using tree detection model
   - Generates and stores detection results in S3
   - Sends processing status via SNS

4. **Log Export Lambda**
   - Runs daily to collect system metrics
   - Aggregates CloudWatch logs from all components
   - Exports performance metrics to CSV

## Project Structure
```
├── .github/workflows/    # CI/CD pipeline configurations
├── config/              # Configuration files
│   ├── config_aws.py
│   ├── config_model.py
│   ├── config_pre_process.py
│   └── config_sns.py
├── data/               # Data directories
│   ├── input/         # Raw input images
│   ├── lambda-reports/# System performance reports
│   ├── ofsets/        # Offset files
│   ├── output/        # Model output files
│   └── processed_images/
│       ├── input_preprocessed/
│       ├── output/
│       └── splited_images/
├── docker/            # Docker configurations
├── models/            # Model files
│   └── v1/
├── src/              # Source code
│   ├── final-activator/    # Activation Lambda
│   ├── final-logexporter/  # Log export Lambda
│   ├── model_image/        # Model Docker image
│   │   ├── models/
│   │   └── src/
│   └── validator/          # Validation components
```

## Prerequisites

- AWS Account with appropriate permissions
- Python 3.x
- Docker
- Required Python packages (see requirements_pre.txt)

## Configuration

### Environment Variables
```
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=your_region
```

### AWS Resources
- S3 Bucket for image storage
- CloudWatch Log Group
- SNS Topic for notifications
- Lambda functions
- ECR repository for Docker images

## Docker Setup for Pre-processing

The pre-processing module runs inside a Docker container. This container processes input images, converts them, splits them into smaller chunks, and uploads the processed images to S3.

### **Building the Docker Image**

To build the Docker image, navigate to the project root (where the `Dockerfile` is located) and run:

```bash
docker build -t finel_preprocess .
```

### **Running the Docker Container**

To run the pre-processing container, use the following command. Make sure to replace the `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` with your actual AWS credentials.

#### **Windows (PowerShell or CMD)**
```bash
docker run --rm \
  -e AWS_ACCESS_KEY_ID="your_access_key" \
  -e AWS_SECRET_ACCESS_KEY="your_secret_key" \
  -v "your_location:/app/data/input" \
  finel_preprocess
```

#### **Linux/Mac**
```bash
docker run --rm \
  -e AWS_ACCESS_KEY_ID="your_access_key" \
  -e AWS_SECRET_ACCESS_KEY="your_secret_key" \
  -v "your_location:/app/data/input" \
  finel_preprocess
```
replace 'your_location' with the input location.

### **Explanation of the Command**
- `--rm` → Automatically removes the container once it stops.
- `-e AWS_ACCESS_KEY_ID=...` and `-e AWS_SECRET_ACCESS_KEY=...` → Pass AWS credentials as environment variables.
- `-v <local_path>:<container_path>` → Mounts the local input directory to the container.
- `finel_preprocess` → Name of the built Docker image.

This setup ensures that the container processes images from the specified local input folder without creating an empty one inside the container.


## Docker Setup for for model-image deployment

Follow these steps to build and deploy the model Docker image:

1. **Authenticate with Amazon ECR**
```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 204597968057.dkr.ecr.us-east-1.amazonaws.com
```

2. **Build the Docker Image**
```bash
docker build --platform linux/amd64 -t docker-image-model:test .
```

3. **Tag the Image**
```bash
docker tag docker-image-model:test 204597968057.dkr.ecr.us-east-1.amazonaws.com/yotam-tree-image:latest
```

4. **Push to ECR**
```bash
docker push 204597968057.dkr.ecr.us-east-1.amazonaws.com/yotam-tree-image:latest
```

## System Flow

1. **Daily Image Processing**
   - Pre-processing container activates at configured time
   - Processes all images in input folder
   - Generates offset data and image chunks
   - Uploads to S3 designated bucket

2. **Offset Processing**
   - Offset splitter Lambda triggers on offset file upload
   - Creates individual offset files for each image
   - Stores mini-offsets in S3

3. **Tree Detection**
   - Detection Lambda activates for each mini-offset
   - Downloads corresponding image chunks
   - Runs detection model
   - Saves results as shapefiles
   - Sends completion notification

4. **Logging and Monitoring**
   - All components log to CloudWatch
   - Daily log export to CSV
   - SNS notifications for system events
   - Processing status tracking via S3 object creation events

## Monitoring and Logging

- All components write to a unified CloudWatch log group
- Daily performance metrics export
- SNS notifications for system events
- Processing status tracking via S3 object creation events

## CI/CD Pipeline

The system includes automated deployment pipeline that:
- Updates Lambda functions when new code is pushed
- Validates configurations
- Manages dependencies
- Sends notifications on successful deployments

## Error Handling

- Failed processing attempts are logged to CloudWatch
- Error notifications sent via SNS
- Automatic retry mechanism for failed operations
- Error logs exported in daily reports

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License



## Contact

@YotamAflalo - yotam.aflalo433@gmail.com
@roy2392 - roey.zalta@gmail.com

