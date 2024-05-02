import json
import os
import time

from pyflink.common import WatermarkStrategy
from pyflink.common.serialization import DeserializationSchema, SerializationSchema, SimpleStringSchema
from pyflink.common.typeinfo import Types
from pyflink.datastream import StreamExecutionEnvironment, WindowFunction
from pyflink.datastream.connectors import DeliveryGuarantee
from pyflink.datastream.connectors.kafka import KafkaSource, \
    KafkaSink, KafkaRecordSerializationSchema, KafkaOffsetsInitializer, KafkaTopicSelector
from pyflink.java_gateway import get_gateway

import character_dialogue
import audio_generator


class BinaryDeserializationSchema(DeserializationSchema):
    def deserialize(self, message: bytes):
        # Directly return the binary message
        return message

    def is_end_of_stream(self, next_element):
        # End of stream is not defined for continuous message consumption
        return False

    def get_produced_type(self):
        # Return the type information for the deserialized data
        return Types.PRIMITIVE_ARRAY(Types.BYTE())


class JsonSerializationSchema(SerializationSchema):
    def serialize(self, value):
        return json.dumps(value)


class BytesSerializationSchema(SerializationSchema):
    def serialize(self, value):
        print('serializer:', value)
        return str(value)


class KeyValueSerializationSchema(SerializationSchema):
    def serialize(self, value):
        # Assuming `value` is a tuple (key, value)
        key, val = value
        # Serialize key and value as bytes, separated by a comma (for example)
        return (key.encode('utf-8'), val.encode('utf-8'))


def initial_greeting(conversation_id):
    t1 = time.time()
    print(0.0, 'received call, generating initial greeting')
    # greeting = character_dialogue.get_initial_greeting("arnold schwartzenegger", "homer simpson")
    greeting = 'test'
    print(time.time() - t1, 'initial greeting generated:', greeting)
    audio = audio_generator.get_response_audio("homer simpson", greeting)
    # audio = bytearray([1, 2, 3])
    print(time.time() - t1, 'audio generated:', len(audio))
    key = json.dumps({'conversationId': conversation_id}).encode('utf-8')
    return key, audio


if __name__ == "__main__":
    # Kafka configuration
    conversations_topic = "haystack-voice-vishing-ai-conversations"
    output_topic = "haystack-voice-vishing-ai-output"
    bootstrap_servers = "pkc-56d1g.eastus.azure.confluent.cloud:9092"
    group_id = "vishing-chat-group"

    env = StreamExecutionEnvironment.get_execution_environment()
    print('Flink parallelism:', env.get_parallelism())

    home_dir = os.path.expanduser('~')
    # env.add_jars(f"file://{home_dir}/.m2/repository/org/apache/flink/flink-connector-kafka/3.1.0-1.18/flink-connector-kafka-3.1.0-1.18.jar")
    # env.add_jars(f"file://{home_dir}/.m2/repository/org/apache/kafka/kafka-clients/3.3.1/kafka-clients-3.3.1.jar")
    working_dir = os.getcwd()
    # env.add_jars(f"file://{home_path}/GoodLabs/GMM_voiceID/java/target/gmm-flink-java-1.0-SNAPSHOT.jar")
    jar_path = f"file://{working_dir}/java/target/gmm-flink-java-1.0-SNAPSHOT.jar"
    env.add_jars(jar_path)
    print(f'added jar {jar_path}')

    gate_way = get_gateway()
    j_char_set = gate_way.jvm.java.nio.charset.Charset.forName('UTF-8')
    j_simple_string_serialization_schema = gate_way \
        .jvm.org.apache.flink.api.common.serialization.SimpleStringSchema(j_char_set)
    j_byte_array_deserialization_schema = gate_way \
        .jvm.studio.goodlabs.vishing.KafkaMapByteArrayDeserializationSchema()
    j_byte_array_serialization_schema = gate_way \
        .jvm.studio.goodlabs.vishing.KafkaValueSerializationSchema()
    j_json_serialization_schema = gate_way \
        .jvm.org.apache.flink.formats.json.JsonSerializationSchema()

    kafka_user = os.environ["KAFKA_GENESYS_CHAT_USER"]
    kafka_password = os.environ["KAFKA_GENESYS_CHAT_PASSWORD"]

    kafka_source = KafkaSource.builder() \
        .set_bootstrap_servers(bootstrap_servers) \
        .set_topics(conversations_topic) \
        .set_group_id(group_id) \
        .set_starting_offsets(KafkaOffsetsInitializer.latest()) \
        .set_deserializer(BinaryDeserializationSchema(j_deserialization_schema=j_byte_array_deserialization_schema)) \
        .set_property('security.protocol', 'SASL_SSL') \
        .set_property('sasl.mechanism', 'PLAIN') \
        .set_property('sasl.jaas.config', f'org.apache.kafka.common.security.plain.PlainLoginModule required username="{kafka_user}" password="{kafka_password}";') \
        .set_property('ssl.ca.location', 'ISRG Root X1.crt') \
        .build()

    key_value_kafka_serialization_schema = KafkaRecordSerializationSchema.builder() \
        .set_topic(output_topic) \
        .set_key_serialization_schema(BytesSerializationSchema(j_serialization_schema=j_byte_array_serialization_schema)) \
        .set_value_serialization_schema(BytesSerializationSchema(j_serialization_schema=j_byte_array_serialization_schema)) \
        .build()

    kafka_sink = KafkaSink.builder() \
        .set_bootstrap_servers(bootstrap_servers) \
        .set_record_serializer(key_value_kafka_serialization_schema) \
        .set_delivery_guarantee(DeliveryGuarantee.NONE) \
        .set_property('security.protocol', 'SASL_SSL') \
        .set_property('sasl.mechanism', 'PLAIN') \
        .set_property('sasl.jaas.config', f'org.apache.kafka.common.security.plain.PlainLoginModule required username="{kafka_user}" password="{kafka_password}";') \
        .set_property('ssl.ca.location', 'ISRG Root X1.crt') \
        .build()

    ds = env.from_source(source=kafka_source,
                         watermark_strategy=WatermarkStrategy.no_watermarks(),
                         source_name="KafkaSource")

    # inference stream
    ds \
        .filter(lambda message: json.loads(message['key'].decode('utf-8'))['type'] == 'open') \
        .key_by(lambda message: json.loads(message['key'].decode('utf-8'))['conversationId'], Types.STRING()) \
        .map(lambda message: initial_greeting(json.loads(message['key'].decode('utf-8'))['conversationId'])) \
        .sink_to(kafka_sink)

    print('starting Flink job')
    env.execute("genesys-chat")
