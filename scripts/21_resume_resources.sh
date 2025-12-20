#!/bin/bash
# scripts/21_resume_resources.sh
# Resumes resources: Starts RDS, Scales ASG to 4 (Budget Friendly), Starts ECS Services.

source infra_ids.env

CLUSTER_NAME="learning-platform-cluster"
ASG_NAME="learning-platform-asg"
DB_IDENTIFIER="learning-platform-db"
ALL_SERVICES="kafka zookeeper auth-service chat-service document-service quiz-service tts-service stt-service api-gateway"

echo "========================================================"
echo "           RESUMING AWS RESOURCES                       "
echo "========================================================"

# 1. Start RDS Instance
echo "[1/3] Starting RDS Database..."
DB_STATUS=$(aws rds describe-db-instances --db-instance-identifier $DB_IDENTIFIER --query "DBInstances[0].DBInstanceStatus" --output text)

if [ "$DB_STATUS" == "stopped" ]; then
    aws rds start-db-instance --db-instance-identifier $DB_IDENTIFIER > /dev/null
    echo "RDS start signal sent. Waiting for 'available' state (this may take minutes)..."
    aws rds wait db-instance-available --db-instance-identifier $DB_IDENTIFIER
    echo "RDS is now AVAILABLE."
elif [ "$DB_STATUS" == "available" ]; then
    echo "RDS is already available."
else
    echo "RDS status is $DB_STATUS. Attempting to proceed..."
fi

# 2. Scale up ASG
# We use 4 instances as calculated to fit "1-5$ a day" budget ($4/day) while supporting 9 services.
echo "[2/3] Scaling Auto Scaling Group to 4 (Cost Optimized)..."
aws autoscaling update-auto-scaling-group --auto-scaling-group-name $ASG_NAME \
    --min-size 1 --max-size 5 --desired-capacity 5
echo "ASG scaled to 4. Waiting for instances to join cluster..."

# Simple wait loop
echo "Waiting 60s for EC2 initialization..."
sleep 60

# 3. Scale up ECS Services
echo "[3/3] Starting ECS Services..."
for SVC in $ALL_SERVICES; do
    echo "  - Starting $SVC..."
    aws ecs update-service --cluster $CLUSTER_NAME --service $SVC --desired-count 1 > /dev/null
done

echo "========================================================"
echo "           RESOURCES RESUMED SUCCESSFULLY               "
echo "========================================================"
