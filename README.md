# monkey-jacket-chat

Compile dependency:

cd /java
mvn clean install

Need to pull monkey-jacket-avatar code at:
https://github.com/goodlabs-studio/monkey-jacket-patient-avatar

and install dependencies in requirement.txt for that project

## Run

    source venv/bin/activate
    python3 flink_chat1.py


#### Needed environment variables


- export MONKEY_JACKET_AVATAR_BASE_PATH=<path_to_monkey_jacket_avatar_module_on_file_system>
- export PYTHONPATH="${PYTHONPATH}:/${MONKEY_JACKET_AVATAR_BASE_PATH}"

- export JAR_DEPENDENCY_PATH=<./java/target/flink-serializers-1.0-SNAPSHOT.jar> 
- export OPENAI_API_KEY="openai api_key"

- export PHYSICIAN_TRANSCRIPT_TOPIC="monkeyjacket-physician-incoming-transcript"
- export PATIENT_TRANSCRIPT_OUTPUT_TOPIC="monkeyjacket-patient-outgoing-transcript"
- export KAFKA_BOOTSTRAP_SERVER="pkc-56d1g.eastus.azure.confluent.cloud:9092"
- export CONVERSATION_ENGINE_GROUP_ID=“monkey-jacket-group”
- export PATIENT_TRANSCRIPT_OUTPUT_TOPIC="monkeyjacket-patient-outgoing-transcript"
- export KAFKA_CHAT_USER="<>"
- export KAFKA_CHAT_PASSWORD="<>"


### Need to patch ####

add following method:

    def set_deserializer(self, deserialization_schema: DeserializationSchema) \
        -> 'KafkaSourceBuilder':
        self._j_builder.setDeserializer(deserialization_schema._j_deserialization_schema)
        return self


to /pyflink/datastream/connectors/kafka.py

in order for deserializers to work properly

## 
