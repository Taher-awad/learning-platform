#!/bin/bash
# scripts/20_pause_resources.sh
# Pauses all cost-incurring resources: ECS Services, Auto Scaling Group, and RDS.

source infra_ids.env

CLUSTER_NAME="learning-platform-cluster"
ASG_NAME="learning-platform-asg"
DB_IDENTIFIER="learning-platform-db"
SERVICES="auth-service chat-service document-service quiz-service tts-service stt-service api-gateway" # kafka/zookeeper managed separately or let them die with instances? Better to stop them too.
ALL_SERVICES="auth-service chat-service document-service quiz-service tts-service stt-service api-gateway kafka zookeeper"

echo "========================================================"
echo "           PAUSING AWS RESOURCES (COST SAVING)          "
echo "========================================================"

# 1. Scale down ECS Services to 0
echo "[1/3] Scaling down ECS Services to 0..."
for SVC in $ALL_SERVICES; do
    echo "  - Stopping $SVC..."
    aws ecs update-service --cluster $CLUSTER_NAME --service $SVC --desired-count 0 > /dev/null
done
echo "All services set to desired-count 0."

# 2. Scale down ASG to 0
echo "[2/3] Scaling Auto Scaling Group to 0..."
aws autoscaling update-auto-scaling-group --auto-scaling-group-name $ASG_NAME \
    --min-size 0 --max-size 0 --desired-capacity 0
echo "ASG scaled to 0. EC2 instances will be terminated."

# 3. Stop RDS Instance
echo "[3/3] Stopping RDS Database..."
DB_STATUS=$(aws rds describe-db-instances --db-instance-identifier $DB_IDENTIFIER --query "DBInstances[0].DBInstanceStatus" --output text)

if [ "$DB_STATUS" == "available" ]; then
    aws rds stop-db-instance --db-instance-identifier $DB_IDENTIFIER > /dev/null
    echo "RDS stop signal sent. Status: $DB_STATUS -> stopping."
elif [ "$DB_STATUS" == "stopped" ]; then
    echo "RDS is already stopped."
else
    echo "RDS status is $DB_STATUS. Cannot stop immediately (might be in transition)."
fi

echo "========================================================"
echo "           RESOURCES PAUSED SUCCESSFULLY                "
echo "========================================================"
