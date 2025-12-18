import sys
import os
import json
import uuid
from confluent_kafka import Consumer, KafkaException, KafkaError

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)

def monitor_kafka():
    print("====================================================")
    print("   KAFKA LIVE MONITOR")
    print("====================================================")
    print("Listening for messages on all topics...")
    print("Press Ctrl+C to stop.")
    print("----------------------------------------------------")

    bootstrap_servers = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    # Inside docker it might be kafka:29092, from host usually localhost:9092 
    # The user runs this from host, so localhost:9092 is correct since we exposed ports.
    
    # Use random group ID to avoid rebalance delays and always read fresh
    group_id = f'monitor-{uuid.uuid4()}'
    
    conf = {
        'bootstrap.servers': bootstrap_servers,
        'group.id': group_id,
        'auto.offset.reset': 'earliest'
    }

    try:
        consumer = Consumer(conf)
    except Exception as e:
        print(f"Failed to create consumer: {e}")
        print("Ensure Kafka is running and accessible at localhost:9092")
        input("Press Enter to exit...")
        return

    topics = [
        "document.uploaded", "document.processed", "notes.generated",
        "quiz.requested", "quiz.generated",
        "audio.transcription.requested", "audio.transcription.completed",
        "audio.generation.requested", "audio.generation.completed",
        "chat.message"
    ]

    try:
        consumer.subscribe(topics)
    except Exception as e:
        print(f"Failed to subscribe: {e}")
        return

    print("Listening for messages on all topics... (Live Mode)", flush=True)

    try:
        while True:
            # Poll faster (0.1s) for lower latency
            msg = consumer.poll(timeout=0.1)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                elif msg.error().code() == KafkaError.UNKNOWN_TOPIC_OR_PART:
                    # Ignore unknown topic error, they might be created later
                    continue
                else:
                    print(msg.error(), flush=True)
                    continue

            try:
                # Pretty print details
                topic = msg.topic()
                key = msg.key().decode('utf-8') if msg.key() else "None"
                value = msg.value().decode('utf-8') if msg.value() else "None"
                
                # Try to format JSON if possible for readability
                try:
                    val_json = json.loads(value)
                    value = json.dumps(val_json, indent=2)
                except:
                    pass

                print(f"\n[TOPIC: {topic}]", flush=True)
                print(f"KEY: {key}", flush=True)
                print(f"VALUE: {value}", flush=True)
                print("-" * 30, flush=True)

            except Exception as e:
                print(f"Error decoding message: {e}", flush=True)

    except KeyboardInterrupt:
        print("\nStopping monitor...")
    finally:
        consumer.close()

if __name__ == "__main__":
    monitor_kafka()
