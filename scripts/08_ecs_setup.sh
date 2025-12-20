#!/bin/bash
set -e

echo "Starting Phase 2: ECS Setup..."

# Load infrastructure IDs
if [ -f "infra_ids.env" ]; then
    source infra_ids.env
else
    echo "ERROR: infra_ids.env not found!"
    exit 1
fi

REGION=$(aws configure get region)
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
SUBNET_IDS="${SUBNET_ID_APP_1},${SUBNET_ID_APP_2}"
ALB_ARN=$(aws elbv2 describe-load-balancers --names learning-platform-alb --query 'LoadBalancers[0].LoadBalancerArn' --output text)
TARGET_GROUP_ARN=$(aws elbv2 describe-target-groups --names learning-platform-app-tg --query 'TargetGroups[0].TargetGroupArn' --output text)
EXECUTION_ROLE_ARN="arn:aws:iam::593223146892:role/learning-platform-ecs-execution-role"
SECURITY_GROUP_ID="$SG_APP_ID"
CLUSTER_NAME="learning-platform-cluster"

# Load Namespace ID
if [ -f "scripts/.namespace_id" ]; then
    source scripts/.namespace_id
elif [ -f ".namespace_id" ]; then
    source .namespace_id
else
    NAMESPACE_ID="ns-luepfneqnidymqym" # Fallback (should prevent error if file missing but might fail if ID wrong)
    echo "WARNING: .namespace_id not found, using valid hardcoded ID: $NAMESPACE_ID"
fi


# 1. Create Cluster
echo "Creating ECS Cluster..."
aws ecs create-cluster --cluster-name $CLUSTER_NAME

# 2. Register Task Definitions & Create Services
SERVICES=(
    "zookeeper:2181"
    "kafka:9092"
    "chat-service:8000"
    "document-service:8000"
    "quiz-service:8000"
    "tts-service:8000"
    "stt-service:8000"
    "auth-service:8000"
    "api-gateway:8000"
)

for SERVICE_INFO in "${SERVICES[@]}"; do
    NAME="${SERVICE_INFO%%:*}"
    PORT="${SERVICE_INFO##*:}"
    IMAGE="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/phase2/${NAME}:latest"
    unset COMMAND
    
    echo "Registering Task Definition for $NAME..."
    
    # Determine DB Host based on service name
    # Determine DB Host based on service name
    DB_IDENTIFIER=""
    if [[ "$NAME" == "chat-service" ]]; then
        DB_IDENTIFIER="learning-platform-db"
        DB_NAME="chatdb"
    elif [[ "$NAME" == "document-service" ]]; then
        DB_IDENTIFIER="learning-platform-db"
        DB_NAME="docdb"
    elif [[ "$NAME" == "quiz-service" ]]; then
        DB_IDENTIFIER="learning-platform-db"
        DB_NAME="quizdb"
    elif [[ "$NAME" == "auth-service" ]]; then
        DB_IDENTIFIER="learning-platform-db"
        DB_NAME="userdb"
    else
        DB_HOST="" # Not a DB service or uses non-standard logic
    fi

    if [ -n "$DB_IDENTIFIER" ]; then
        echo "Fetching endpoint for $DB_IDENTIFIER..."
        DB_HOST=$(aws rds describe-db-instances --db-instance-identifier $DB_IDENTIFIER --query 'DBInstances[0].Endpoint.Address' --output text)
        if [ "$DB_HOST" == "None" ] || [ -z "$DB_HOST" ]; then
             echo "ERROR: Could not fetch endpoint for $DB_IDENTIFIER. Is the DB created?"
             exit 1
        fi
    fi
    # Determine Image and Env Vars
    # Load Secrets ARN
    if [ -f "scripts/.secrets_config" ]; then
        source scripts/.secrets_config
    elif [ -f ".secrets_config" ]; then
        source .secrets_config
    fi
    
    # Base Secrets (Common to most services) -> Using 'secrets' block instead of 'environment'
    # ValueFrom syntax: arn:aws:secretsmanager:region:account:secret:name:json_key::
    
    if [[ "$NAME" == "minio" ]]; then
       continue
    fi

    SECRETS_BLOCK="[]"
    
    if [[ "$NAME" == "zookeeper" ]]; then
        IMAGE="confluentinc/cp-zookeeper:7.5.0"
        ENV_VARS='[{"name": "ZOOKEEPER_CLIENT_PORT", "value": "2181"}, {"name": "ZOOKEEPER_TICK_TIME", "value": "2000"}]'
    elif [[ "$NAME" == "kafka" ]]; then
        IMAGE="confluentinc/cp-kafka:7.5.0"
        ENV_VARS='[
            {"name": "KAFKA_BROKER_ID", "value": "1"},
            {"name": "KAFKA_ZOOKEEPER_CONNECT", "value": "zookeeper.learning-platform.local:2181"},
            {"name": "KAFKA_ADVERTISED_LISTENERS", "value": "PLAINTEXT://kafka.learning-platform.local:9092"},
            {"name": "KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR", "value": "1"}
        ]'
    else
        IMAGE="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/phase2/${NAME}:latest"
        
        # Non-sensitive Env Vars
        ENV_VARS="[
            {\"name\": \"POSTGRES_HOST\", \"value\": \"$DB_HOST\"},
            {\"name\": \"POSTGRES_USER\", \"value\": \"dbadmin\"},
            {\"name\": \"POSTGRES_DB\", \"value\": \"$DB_NAME\"},
            {\"name\": \"DATABASE_URL\", \"value\": \"postgresql://dbadmin:ChangeMe123@$DB_HOST:5432/$DB_NAME?sslmode=require\"},
            {\"name\": \"S3_BUCKET_NAME\", \"value\": \"learning-platform-${NAME/service/storage}-dev-${ACCOUNT_ID}\"},
            {\"name\": \"AWS_REGION\", \"value\": \"$REGION\"},
            {\"name\": \"KAFKA_BOOTSTRAP_SERVERS\", \"value\": \"kafka.learning-platform.local:9092\"}
        ]"

        # Secrets Block
        if [ -n "$SECRET_ARN" ]; then
            SECRETS_BLOCK="[
                {\"name\": \"POSTGRES_PASSWORD\", \"valueFrom\": \"${SECRET_ARN}:DB_PASSWORD::\"},
                {\"name\": \"ELEVENLABS_API_KEY\", \"valueFrom\": \"${SECRET_ARN}:ELEVENLABS_API_KEY::\"},
                {\"name\": \"GOOGLE_API_KEY\", \"valueFrom\": \"${SECRET_ARN}:GEMINI_API_KEY::\"},
                {\"name\": \"JWT_SECRET\", \"valueFrom\": \"${SECRET_ARN}:JWT_SECRET::\"}
            ]"
        else
            echo "WARNING: SECRET_ARN not found. Using hardcoded details (INSECURE)."
            ENV_VARS="${ENV_VARS::-1}, 
                {\"name\": \"POSTGRES_PASSWORD\", \"value\": \"ChangeMe123\"},
                {\"name\": \"PGSSLMODE\", \"value\": \"require\"},
                {\"name\": \"DATABASE_URL\", \"value\": \"postgresql://dbadmin:ChangeMe123@${DB_HOST}:5432/${DB_NAME}?sslmode=require\"},
                {\"name\": \"ELEVENLABS_API_KEY\", \"value\": \"sk_ce8d69513338b3010ee8eef3cc1616ef1ca1ad520340fce7\"},
                {\"name\": \"GOOGLE_API_KEY\", \"value\": \"AIzaSyBt_azQNz0w-vcyNEQu-tbB__pKIri6EpU\"}
            ]"
        fi
    fi
    
    echo "Registering Task Definition for $NAME..."

    TASK_DEF=$(cat <<EOF
{
    "family": "$NAME",
    "networkMode": "awsvpc",
    "containerDefinitions": [
        {
            "name": "$NAME",
            "image": "$IMAGE",
            "portMappings": [
                {
                    "containerPort": $PORT,
                    "hostPort": $PORT,
                    "protocol": "tcp"
                }
            ],
            "essential": true,
            "command": ${COMMAND:-[]},
            "environment": $ENV_VARS,
            "secrets": $SECRETS_BLOCK,
            "memoryReservation": 256,
            "logConfiguration": {
                "logDriver": "awslogs",
                "options": {
                    "awslogs-group": "/ecs/$NAME",
                    "awslogs-region": "$REGION",
                    "awslogs-stream-prefix": "ecs"
                }
            }
        }
    ],
    "requiresCompatibilities": ["EC2"],
    "cpu": "256",
    "memory": "512",
    "executionRoleArn": "$EXECUTION_ROLE_ARN",
    "taskRoleArn": "$EXECUTION_ROLE_ARN"
}
EOF
)

    # Create Log Group
    aws logs create-log-group --log-group-name "/ecs/$NAME" || true

    # Register Task
    aws ecs register-task-definition --cli-input-json "$TASK_DEF" > /dev/null

    # Create or Update Service
    echo "Deploying Service $NAME..."
    
    # Check if service exists
    SERVICE_EXISTS=$(aws ecs describe-services --cluster $CLUSTER_NAME --services $NAME --query 'services[0].status' --output text)
    
    if [ "$SERVICE_EXISTS" == "ACTIVE" ]; then
        echo "Updating Service $NAME..."
        aws ecs update-service --cluster $CLUSTER_NAME --service $NAME --task-definition $NAME --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_IDS],securityGroups=[$SECURITY_GROUP_ID]}" --force-new-deployment > /dev/null
    else
        echo "Creating Service $NAME..."

        if [[ "$NAME" == "api-gateway" ]]; then
            # Check if Service Discovery Service exists, if not create it
            SD_SERVICE_ARN=$(aws servicediscovery list-services --filters Name=NAMESPACE_ID,Values=$NAMESPACE_ID --query "Services[?Name=='$NAME'].Arn" --output text)
            if [ -z "$SD_SERVICE_ARN" ]; then
                 SD_SERVICE_ARN=$(aws servicediscovery create-service --name $NAME --dns-config 'DnsRecords=[{Type=A,TTL=60}]' --namespace-id $NAMESPACE_ID --query 'Service.Arn' --output text)
            fi
    
            aws ecs create-service \
                --cluster $CLUSTER_NAME \
                --service-name $NAME \
                --task-definition $NAME \
                --desired-count 1 \
                --launch-type EC2 \
                --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_IDS],securityGroups=[$SECURITY_GROUP_ID]}" \
                --load-balancers "targetGroupArn=$TARGET_GROUP_ARN,containerName=$NAME,containerPort=$PORT" \
                --service-registries "registryArn=$SD_SERVICE_ARN"
        else
            # Check if Service Discovery Service exists, if not create it
            SD_SERVICE_ARN=$(aws servicediscovery list-services --filters Name=NAMESPACE_ID,Values=$NAMESPACE_ID --query "Services[?Name=='$NAME'].Arn" --output text)
            if [ -z "$SD_SERVICE_ARN" ]; then
                 SD_SERVICE_ARN=$(aws servicediscovery create-service --name $NAME --dns-config 'DnsRecords=[{Type=A,TTL=60}]' --namespace-id $NAMESPACE_ID --query 'Service.Arn' --output text)
            fi
    
            aws ecs create-service \
                --cluster $CLUSTER_NAME \
                --service-name $NAME \
                --task-definition $NAME \
                --desired-count 1 \
                --launch-type EC2 \
                --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_IDS],securityGroups=[$SECURITY_GROUP_ID]}" \
                --service-registries "registryArn=$SD_SERVICE_ARN"
        fi
    fi
done

echo "ECS Setup Complete!"
