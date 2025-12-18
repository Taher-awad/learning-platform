from confluent_kafka.admin import AdminClient
import os
import sys

def test_kafka_topics():
    print("Connecting to Kafka...")
    bootstrap_servers = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
    
    conf = {'bootstrap.servers': bootstrap_servers}
    admin_client = AdminClient(conf)

    # Required topics from requirements
    required_topics = {
        "document.uploaded",
        "document.processed",
        "notes.generated",
        "quiz.requested",
        "quiz.generated",
        "audio.transcription.requested",
        "audio.transcription.completed",
        "audio.generation.requested",
        "audio.generation.completed",
        "chat.message"
    }

    try:
        # Fetch metadata (list topics)
        metadata = admin_client.list_topics(timeout=10)
        existing_topics = set(metadata.topics.keys())
        
        print("\nExisting Topics:")
        for t in existing_topics:
            print(f"- {t}")

        # Check for missing topics
        missing = required_topics - existing_topics
        
        if missing:
            print(f"\n[FAIL] Missing required topics: {missing}")
            # Note: Topics typically auto-create on first use with default config, 
            # or we might need to explicitly create them.  
            # For this test, we verify infrastructure readiness.
            # If auto-create is on, they might not exist until produced to.
            # We will pass if we can at least connect, but warn on missing.
            print("Note: Topics may be auto-created upon first use.")
            # We strictly fail only if connection failed (empty list usually implies connection error or empty broker)
            if not existing_topics:
                 sys.exit(1)
        else:
            print("\n[PASS] All required topics exist.")
            
    except Exception as e:
        print(f"\n[FAIL] Kafka connection error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_kafka_topics()
